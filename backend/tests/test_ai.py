from app.ai.client import FakeLLM, LLMParseError
from app.ai.orchestrator import generate_ai_plan, hydrate_plan
from app.ai.prompts import CURRENT_WORKOUT_PLAN_PROMPT
from app.ai.schemas import LLMExercisePrescription, LLMWorkoutDay, LLMWorkoutPlan
from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.types import WorkoutPlan
from app.engine.validate import validate_plan
from tests.test_engine import beginner_no_barbell


def _as_llm_plan(plan: WorkoutPlan, *, broken_id: str | None = None) -> LLMWorkoutPlan:
    days = []
    for day in plan.days:
        exercises = []
        for index, prescription in enumerate(day.exercises):
            exercise_id = prescription.exercise_id
            if broken_id and index == 0 and day.day_index == 0:
                exercise_id = broken_id
            exercises.append(
                LLMExercisePrescription(
                    exercise_id=exercise_id,
                    sets=prescription.sets,
                    rep_min=prescription.rep_min,
                    rep_max=prescription.rep_max,
                    target_rir=prescription.target_rir,
                    target_weight_kg=prescription.target_weight_kg,
                )
            )
        days.append(
            LLMWorkoutDay(
                day_index=day.day_index,
                label=day.label,
                focus=day.focus,
                exercises=exercises,
            )
        )
    return LLMWorkoutPlan(
        days_per_week=plan.days_per_week,
        split=plan.split,
        days=days,
        reasoning=plan.reasoning,
    )


def test_valid_structured_output_is_used() -> None:
    constraints = beginner_no_barbell()
    valid = _as_llm_plan(generate_plan(constraints, CATALOG))
    result = generate_ai_plan(constraints, CATALOG, llm=FakeLLM([valid]))
    assert result.generation.source == "llm"
    assert result.generation.prompt_version == CURRENT_WORKOUT_PLAN_PROMPT
    assert result.generation.attempts == 1
    assert validate_plan(result.plan, constraints, CATALOG) == []


def test_invalid_output_retries_then_succeeds() -> None:
    constraints = beginner_no_barbell()
    engine_plan = generate_plan(constraints, CATALOG)
    invalid = _as_llm_plan(engine_plan, broken_id="not_a_real_lift")
    valid = _as_llm_plan(engine_plan)
    llm = FakeLLM([invalid, valid])
    result = generate_ai_plan(constraints, CATALOG, llm=llm)
    assert result.generation.source == "llm"
    assert result.generation.attempts == 2
    assert result.generation.attempt_errors
    assert "not_a_real_lift" not in [
        item.exercise_id for day in result.plan.days for item in day.exercises
    ]
    assert len(llm.calls) == 2
    assert "failed validation" in llm.calls[1][-1]["content"]


def test_invalid_output_falls_back_to_engine() -> None:
    constraints = beginner_no_barbell()
    invalid = _as_llm_plan(generate_plan(constraints, CATALOG), broken_id="totally_invented")
    result = generate_ai_plan(
        constraints,
        CATALOG,
        llm=FakeLLM([invalid, invalid, invalid]),
    )
    assert result.generation.source == "fallback"
    assert result.generation.fallback_reason == "llm_failed"
    assert result.generation.attempts == 3
    assert validate_plan(result.plan, constraints, CATALOG) == []
    ids = [item.exercise_id for day in result.plan.days for item in day.exercises]
    assert "totally_invented" not in ids


def test_parse_failure_falls_back() -> None:
    constraints = beginner_no_barbell()
    result = generate_ai_plan(
        constraints,
        CATALOG,
        llm=FakeLLM([LLMParseError("bad json"), LLMParseError("still bad"), LLMParseError("nope")]),
    )
    assert result.generation.source == "fallback"
    assert result.generation.fallback_reason == "llm_failed"
    assert validate_plan(result.plan, constraints, CATALOG) == []


def test_missing_llm_falls_back_without_calling_model() -> None:
    constraints = beginner_no_barbell()
    result = generate_ai_plan(constraints, CATALOG, llm=None)
    assert result.generation.source == "fallback"
    assert result.generation.fallback_reason == "llm_unavailable"
    assert result.generation.attempts == 0
    assert validate_plan(result.plan, constraints, CATALOG) == []


def test_hydrate_recomputes_duration() -> None:
    constraints = beginner_no_barbell()
    llm_plan = _as_llm_plan(generate_plan(constraints, CATALOG))
    hydrated = hydrate_plan(llm_plan, CATALOG)
    assert all(day.estimated_minutes > 0 for day in hydrated.days)
    assert validate_plan(hydrated, constraints, CATALOG) == []


def test_ai_plan_http_endpoint_uses_llm() -> None:
    from fastapi.testclient import TestClient

    from app.api import get_structured_llm
    from app.main import app

    valid = _as_llm_plan(generate_plan(beginner_no_barbell(), CATALOG))
    app.dependency_overrides[get_structured_llm] = lambda: FakeLLM([valid])
    client = TestClient(app)
    try:
        created = client.post(
            "/v1/users",
            json={
                "name": "Riya",
                "days_per_week": 3,
                "max_duration_minutes": 45,
                "available_equipment": [
                    "dumbbell",
                    "cable",
                    "machine",
                    "bodyweight",
                    "kettlebell",
                    "band",
                ],
                "goal": "hypertrophy",
                "training_age": "beginner",
            },
        )
        user_id = created.json()["id"]
        response = client.post(f"/v1/users/{user_id}/plan/ai")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["generation"]["source"] == "llm"
        assert body["generation"]["prompt_version"] == CURRENT_WORKOUT_PLAN_PROMPT
        assert body["violations"] == []
    finally:
        app.dependency_overrides.clear()


def test_ai_plan_http_falls_back_without_api_key() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    created = client.post(
        "/v1/users",
        json={
            "name": "Riya",
            "days_per_week": 3,
            "max_duration_minutes": 45,
            "available_equipment": [
                "dumbbell",
                "cable",
                "machine",
                "bodyweight",
                "kettlebell",
                "band",
            ],
            "goal": "hypertrophy",
            "training_age": "beginner",
        },
    )
    user_id = created.json()["id"]
    response = client.post(f"/v1/users/{user_id}/plan/ai")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["generation"]["source"] == "fallback"
    assert body["generation"]["fallback_reason"] == "llm_unavailable"
    assert body["violations"] == []
