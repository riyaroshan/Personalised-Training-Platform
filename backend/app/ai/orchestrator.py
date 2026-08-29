from __future__ import annotations

from pydantic import BaseModel

from app.ai.client import LLMParseError, StructuredLLM, build_llm
from app.ai.prompts import get_prompt, render_user_prompt
from app.ai.schemas import GenerationMeta, LLMWorkoutPlan
from app.config import settings
from app.engine.catalog import Catalog
from app.engine.duration import estimate_minutes
from app.engine.generator import generate_plan
from app.engine.types import (
    ExercisePrescription,
    UserConstraints,
    WorkoutPlan,
    WorkoutPlanDay,
    WorkoutSetLog,
)
from app.engine.validate import validate_plan


class AIPlanResult(BaseModel):
    plan: WorkoutPlan
    generation: GenerationMeta


def generate_ai_plan(
    constraints: UserConstraints,
    catalog: Catalog,
    *,
    history: list[WorkoutSetLog] | None = None,
    sessions_completed: int = 0,
    llm: StructuredLLM | None = None,
    prompt_version: str | None = None,
) -> AIPlanResult:
    prompt = get_prompt(prompt_version or settings.prompt_version)
    client = llm if llm is not None else build_llm()
    history = history or []

    if client is None:
        return _fallback(
            constraints,
            catalog,
            history,
            sessions_completed,
            prompt.id,
            reason="llm_unavailable",
            attempts=0,
            errors=["OPENAI_API_KEY is not set"],
        )

    user_prompt = render_user_prompt(constraints, catalog, history)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": prompt.system},
        {"role": "user", "content": user_prompt},
    ]
    errors: list[str] = []
    input_tokens = 0
    output_tokens = 0
    max_attempts = max(1, settings.llm_max_attempts)

    for attempt in range(1, max_attempts + 1):
        try:
            parsed = client.parse(messages)
        except (LLMParseError, Exception) as exc:
            error = f"parse_error: {exc}"
            errors.append(error)
            messages.append({"role": "user", "content": _retry_message(error)})
            continue

        input_tokens += parsed.input_tokens
        output_tokens += parsed.output_tokens
        plan = hydrate_plan(parsed.parsed, catalog)
        violations = validate_plan(plan, constraints, catalog)
        if not violations:
            return AIPlanResult(
                plan=plan,
                generation=GenerationMeta(
                    source="llm",
                    prompt_version=prompt.id,
                    model=parsed.model,
                    attempts=attempt,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    attempt_errors=errors,
                ),
            )
        error = "; ".join(f"{item.code}: {item.message}" for item in violations)
        errors.append(error)
        messages.append({"role": "user", "content": _retry_message(error)})

    return _fallback(
        constraints,
        catalog,
        history,
        sessions_completed,
        prompt.id,
        reason="llm_failed",
        attempts=max_attempts,
        errors=errors,
        model=getattr(client, "model", None),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def hydrate_plan(llm_plan: LLMWorkoutPlan, catalog: Catalog) -> WorkoutPlan:
    days: list[WorkoutPlanDay] = []
    for day in llm_plan.days:
        prescriptions: list[ExercisePrescription] = []
        known = True
        for item in day.exercises:
            rest = 90
            if item.exercise_id in catalog.by_id:
                rest = catalog.get(item.exercise_id).rest_seconds
            else:
                known = False
            prescriptions.append(
                ExercisePrescription(
                    exercise_id=item.exercise_id,
                    sets=item.sets,
                    rep_min=item.rep_min,
                    rep_max=item.rep_max,
                    target_rir=item.target_rir,
                    target_weight_kg=item.target_weight_kg,
                    rest_seconds=rest,
                )
            )
        minutes = estimate_minutes(prescriptions, catalog) if known and prescriptions else 0
        days.append(
            WorkoutPlanDay(
                day_index=day.day_index,
                label=day.label,
                focus=day.focus,
                estimated_minutes=minutes,
                exercises=prescriptions,
            )
        )
    return WorkoutPlan(
        days_per_week=llm_plan.days_per_week,
        split=llm_plan.split,
        days=days,
        reasoning=llm_plan.reasoning,
    )


def _fallback(
    constraints: UserConstraints,
    catalog: Catalog,
    history: list[WorkoutSetLog],
    sessions_completed: int,
    prompt_version: str,
    *,
    reason: str,
    attempts: int,
    errors: list[str],
    model: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> AIPlanResult:
    plan = generate_plan(
        constraints,
        catalog,
        history=history,
        sessions_completed=sessions_completed,
    )
    return AIPlanResult(
        plan=plan,
        generation=GenerationMeta(
            source="fallback",
            prompt_version=prompt_version,
            model=model,
            attempts=attempts,
            fallback_reason=reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            attempt_errors=errors,
        ),
    )


def _retry_message(error: str) -> str:
    return (
        "That plan failed validation and must not be shown to the user.\n"
        f"Errors:\n{error}\n"
        "Return a new structured plan that fixes every error. "
        "Use only catalog exercise_id values."
    )
