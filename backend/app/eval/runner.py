from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai.agent import ask_coach
from app.ai.tools import ToolContext
from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.types import Equipment, Goal, TrainingAge, UserConstraints, WorkoutSetLog
from app.engine.validate import validate_plan
from app.eval.naive import naive_plan
from app.eval.scenarios import (
    NO_BARBELL,
    CoachScenario,
    PlanScenario,
    RagScenario,
    coach_scenarios,
    plan_scenarios,
    rag_scenarios,
)
from app.rag.answer import answer_question
from app.rag.index import KnowledgeIndex
from app.rag.retrieve import RetrieverConfig

GPT4O_MINI_INPUT = 0.15 / 1_000_000
GPT4O_MINI_OUTPUT = 0.60 / 1_000_000


class CaseResult(BaseModel):
    id: str
    family: Literal["plan", "rag", "coach"]
    variant: str
    passed: bool
    checks: dict[str, bool]
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    detail: dict[str, Any] = Field(default_factory=dict)


class Scorecard(BaseModel):
    cases: int
    passed: int
    constraint_adherence: float
    exercise_validity: float
    grounded_rate: float
    hallucination_rate: float
    avg_latency_ms: float
    cost_per_request: float
    by_family: dict[str, dict[str, float]]
    by_variant: dict[str, dict[str, float]]
    results: list[CaseResult]


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return round(input_tokens * GPT4O_MINI_INPUT + output_tokens * GPT4O_MINI_OUTPUT, 8)


def run_suite(
    *,
    include_naive: bool = True,
    rag_variant: str = "hybrid_rerank",
    index: KnowledgeIndex | None = None,
) -> Scorecard:
    index = index or KnowledgeIndex()
    results: list[CaseResult] = []
    for scenario in plan_scenarios():
        results.append(_eval_plan(scenario, "engine"))
        if include_naive:
            results.append(_eval_plan(scenario, "naive"))
    config = _retriever(rag_variant)
    for scenario in rag_scenarios():
        results.append(_eval_rag(scenario, rag_variant, index, config))
    for scenario in coach_scenarios():
        results.append(_eval_coach(scenario))
    return _scorecard(results)


def compare_retrievers(index: KnowledgeIndex | None = None) -> dict[str, Scorecard]:
    index = index or KnowledgeIndex()
    cards = {}
    for variant in ("semantic", "hybrid", "hybrid_rerank", "injury_filter"):
        results = [_eval_rag(scenario, variant, index, _retriever(variant)) for scenario in rag_scenarios()]
        cards[variant] = _scorecard(results)
    return cards


def _eval_plan(scenario: PlanScenario, variant: str) -> CaseResult:
    start = time.perf_counter()
    plan = (
        generate_plan(scenario.constraints, CATALOG)
        if variant == "engine"
        else naive_plan(scenario.constraints, CATALOG)
    )
    latency = (time.perf_counter() - start) * 1000
    violations = validate_plan(plan, scenario.constraints, CATALOG)
    codes = {item.code for item in violations}
    ids = [item.exercise_id for day in plan.days for item in day.exercises]
    barbell_used = any(
        Equipment.BARBELL in CATALOG.get(exercise_id).equipment
        for exercise_id in ids
        if exercise_id in CATALOG.by_id
    )
    checks = {
        "days": len(plan.days) == scenario.constraints.days_per_week,
        "duration": all(day.estimated_minutes <= scenario.constraints.max_duration_minutes for day in plan.days),
        "valid_exercises": "unknown_exercise" not in codes,
        "equipment": "equipment" not in codes and "no_barbell" not in codes,
        "coverage": "coverage" not in codes,
        "no_barbell": (not barbell_used) if scenario.expect_no_barbell else True,
        "injury": "injury" not in codes,
    }
    return CaseResult(
        id=scenario.id,
        family="plan",
        variant=variant,
        passed=all(checks.values()),
        checks=checks,
        latency_ms=round(latency, 2),
        detail={"violation_codes": sorted(codes), "name": scenario.name},
    )


def _eval_rag(
    scenario: RagScenario,
    variant: str,
    index: KnowledgeIndex,
    config: RetrieverConfig,
) -> CaseResult:
    start = time.perf_counter()
    answer = answer_question(scenario.question, config=config, index=index)
    latency = (time.perf_counter() - start) * 1000
    cited = [item.document_id for item in answer.citations]
    expected_hit = any(doc in cited for doc in scenario.expected_documents)
    forbidden_hit = any(doc in cited for doc in scenario.forbidden_documents)
    checks = {
        "retrieved_expected": expected_hit,
        "cited": bool(answer.citations),
        "no_forbidden": not forbidden_hit,
        "answer_cites_chunk": any(f"[{doc}]" in answer.answer for doc in cited[:3]) if cited else False,
    }
    hallucinated = (not answer.citations) or forbidden_hit
    return CaseResult(
        id=scenario.id,
        family="rag",
        variant=variant,
        passed=all(checks.values()),
        checks=checks,
        latency_ms=round(latency, 2),
        detail={
            "cited": cited,
            "hallucinated": hallucinated,
            "expected": scenario.expected_documents,
        },
    )


def _eval_coach(scenario: CoachScenario) -> CaseResult:
    ctx = _coach_context(scenario.fixture)
    start = time.perf_counter()
    result = ask_coach(scenario.question, ctx, llm=None)
    latency = (time.perf_counter() - start) * 1000
    names = [item["name"] for item in result.tool_calls]
    text = result.answer.lower()
    checks = {
        "grounded": result.grounded,
        "tools": all(name in names for name in scenario.expected_tools),
        "no_pep_talk": not any(phrase in text for phrase in scenario.forbidden_phrases),
        "has_evidence": bool(result.evidence),
    }
    return CaseResult(
        id=scenario.id,
        family="coach",
        variant="heuristic_tools",
        passed=all(checks.values()),
        checks=checks,
        latency_ms=round(latency, 2),
        input_tokens=result.generation.input_tokens,
        output_tokens=result.generation.output_tokens,
        cost_usd=estimate_cost(result.generation.input_tokens, result.generation.output_tokens),
        detail={"tools": names, "source": result.generation.source},
    )


def _coach_context(fixture: str) -> ToolContext:
    now = datetime(2026, 9, 1, tzinfo=UTC)
    history: list[WorkoutSetLog] = []
    if fixture == "bench_decline":
        start = now - timedelta(days=50)
        for week, weight in enumerate((32.0, 30.0, 28.0, 26.0)):
            day = start + timedelta(days=week * 10)
            for set_index in range(3):
                history.append(
                    WorkoutSetLog(
                        exercise_id="db_bench_press",
                        weight_kg=weight,
                        reps=8,
                        rpe=9.0,
                        rir=0,
                        completed_at=day,
                        set_index=set_index,
                    )
                )
    constraints = UserConstraints(
        days_per_week=3,
        max_duration_minutes=45,
        available_equipment=NO_BARBELL,
        injuries=[],
        goal=Goal.HYPERTROPHY,
        training_age=TrainingAge.BEGINNER,
    )
    return ToolContext(
        catalog=CATALOG,
        constraints=constraints,
        history=history,
        workouts=[],
        current_plan=None,
        sessions_completed=0,
        now=now,
    )


def _retriever(variant: str) -> RetrieverConfig:
    if variant == "semantic":
        return RetrieverConfig(hybrid=False, rerank=False, top_k=4, chunk_size=80, contextual=True)
    if variant == "hybrid":
        return RetrieverConfig(hybrid=True, rerank=False, top_k=4, chunk_size=80, contextual=True)
    if variant == "injury_filter":
        return RetrieverConfig(hybrid=True, rerank=True, top_k=4, chunk_size=80, contextual=True, topic="injury")
    return RetrieverConfig(hybrid=True, rerank=True, top_k=4, chunk_size=80, contextual=True)


def _scorecard(results: list[CaseResult]) -> Scorecard:
    def rate(items: list[CaseResult], key: str | None = None) -> float:
        if not items:
            return 0.0
        if key is None:
            return round(sum(1 for item in items if item.passed) / len(items), 4)
        hits = 0
        n = 0
        for item in items:
            if key in item.checks:
                n += 1
                hits += int(item.checks[key])
        return round(hits / n, 4) if n else 0.0

    plans = [item for item in results if item.family == "plan"]
    engine_plans = [item for item in plans if item.variant == "engine"]
    rag = [item for item in results if item.family == "rag"]
    coach = [item for item in results if item.family == "coach"]
    grounded_pool = rag + coach
    grounded_hits = 0
    for item in rag:
        grounded_hits += int(item.checks.get("retrieved_expected") and item.checks.get("cited"))
    for item in coach:
        grounded_hits += int(item.checks.get("grounded", False))
    hallucinated = 0
    for item in rag:
        hallucinated += int(bool(item.detail.get("hallucinated")))
    for item in coach:
        hallucinated += int(not item.checks.get("grounded", False))

    by_family = {
        family: {
            "cases": float(len(group)),
            "pass_rate": rate(group),
            "avg_latency_ms": round(sum(item.latency_ms for item in group) / len(group), 2) if group else 0.0,
        }
        for family, group in (("plan", engine_plans or plans), ("rag", rag), ("coach", coach))
    }
    variants: dict[str, list[CaseResult]] = {}
    for item in results:
        variants.setdefault(item.variant, []).append(item)
    by_variant = {
        name: {"cases": float(len(group)), "pass_rate": rate(group)}
        for name, group in variants.items()
    }
    return Scorecard(
        cases=len(results),
        passed=sum(1 for item in results if item.passed),
        constraint_adherence=rate(engine_plans or plans),
        exercise_validity=rate(engine_plans or plans, "valid_exercises"),
        grounded_rate=round(grounded_hits / len(grounded_pool), 4) if grounded_pool else 0.0,
        hallucination_rate=round(hallucinated / len(grounded_pool), 4) if grounded_pool else 0.0,
        avg_latency_ms=round(sum(item.latency_ms for item in results) / len(results), 2) if results else 0.0,
        cost_per_request=round(sum(item.cost_usd for item in results) / len(results), 8) if results else 0.0,
        by_family=by_family,
        by_variant=by_variant,
        results=results,
    )


def public_scorecard(card: Scorecard) -> dict[str, Any]:
    payload = card.model_dump()
    payload.pop("results")
    payload["failures"] = [
        {"id": item.id, "family": item.family, "variant": item.variant, "checks": item.checks}
        for item in card.results
        if not item.passed and item.variant != "naive"
    ]
    return payload
