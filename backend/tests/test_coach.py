from datetime import UTC, datetime, timedelta

from app.ai.agent import ask_coach
from app.ai.client import FakeAgentLLM
from app.ai.prompts import CURRENT_COACH_PROMPT
from app.ai.tools import TOOL_SCHEMAS, ToolContext, execute_tool, resolve_exercise_ids
from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.types import WorkoutSetLog
from tests.test_engine import beginner_no_barbell


def _now() -> datetime:
    return datetime(2026, 9, 1, tzinfo=UTC)


def _ctx(history: list[WorkoutSetLog] | None = None) -> ToolContext:
    return ToolContext(
        catalog=CATALOG,
        constraints=beginner_no_barbell(),
        history=history or [],
        workouts=[],
        current_plan=None,
        sessions_completed=0,
        now=_now(),
    )


def _bench_history() -> list[WorkoutSetLog]:
    start = _now() - timedelta(days=50)
    rows: list[WorkoutSetLog] = []
    for week, weight in enumerate((32.0, 30.0, 28.0, 26.0)):
        day = start + timedelta(days=week * 10)
        for set_index in range(3):
            rows.append(
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
    return rows


def test_resolve_bench_skips_dips() -> None:
    ids = resolve_exercise_ids("bench", CATALOG)
    assert "db_bench_press" in ids
    assert "bench_dip" not in ids


def test_exercise_history_reports_declining_trend() -> None:
    result = execute_tool(
        "get_exercise_history",
        {"exercise": "bench", "days": 60},
        _ctx(_bench_history()),
    )
    assert result.ok
    assert result.result["trend"] == "declining"
    assert result.result["set_count"] == 12
    assert "db_bench_press" in result.result["matched_exercise_ids"]


def test_all_seven_tools_are_registered() -> None:
    names = {item["function"]["name"] for item in TOOL_SCHEMAS}
    assert names == {
        "get_recent_workouts",
        "get_exercise_history",
        "get_muscle_volume",
        "get_personal_records",
        "get_recovery_scores",
        "find_exercise_substitutes",
        "update_workout_plan",
    }


def test_update_plan_swaps_eligible_exercise() -> None:
    constraints = beginner_no_barbell()
    plan = generate_plan(constraints, CATALOG)
    source = plan.days[0].exercises[0].exercise_id
    ctx = _ctx()
    ctx.current_plan = plan
    result = execute_tool(
        "find_exercise_substitutes",
        {"exercise": source},
        ctx,
    )
    assert result.ok
    assert result.result["substitutes"]
    replacement = result.result["substitutes"][0]["exercise_id"]
    updated = execute_tool(
        "update_workout_plan",
        {"replace_exercise_id": source, "with_exercise_id": replacement},
        ctx,
    )
    assert updated.ok
    assert ctx.persist_plan is True
    assert replacement in [
        item.exercise_id for day in ctx.updated_plan.days for item in day.exercises
    ]


def test_heuristic_bench_question_is_grounded() -> None:
    result = ask_coach("Why hasn't my bench improved?", _ctx(_bench_history()), llm=None)
    names = [item["name"] for item in result.tool_calls]
    assert "get_exercise_history" in names
    assert "get_muscle_volume" in names
    assert "get_recovery_scores" in names
    assert result.grounded is True
    assert result.generation.source == "fallback"
    assert result.generation.prompt_version == CURRENT_COACH_PROMPT
    assert "declining" in result.answer.lower()
    assert any("trend=declining" in line for line in result.evidence)


def test_agent_loop_calls_tools_then_answers() -> None:
    llm = FakeAgentLLM(
        [
            {
                "tool_calls": [
                    {"name": "get_exercise_history", "arguments": {"exercise": "bench", "days": 60}},
                    {"name": "get_muscle_volume", "arguments": {"muscle": "chest", "days": 30}},
                    {"name": "get_recovery_scores", "arguments": {"days": 30}},
                ]
            },
            {"content": '{"answer": "Bench load decreased in the log.", "evidence": ["trend"]}'},
        ]
    )
    result = ask_coach("Why hasn't my bench improved?", _ctx(_bench_history()), llm=llm)
    assert result.generation.source == "llm"
    assert result.generation.prompt_version == CURRENT_COACH_PROMPT
    assert result.grounded is True
    assert "decreased" in result.answer.lower()
    names = [item["name"] for item in result.tool_calls]
    assert names == ["get_exercise_history", "get_muscle_volume", "get_recovery_scores"]
    assert any("trend=declining" in line for line in result.evidence)


def test_ungrounded_answer_falls_back_to_tools() -> None:
    llm = FakeAgentLLM([{"content": '{"answer": "Just try harder next week.", "evidence": []}'}])
    result = ask_coach("Why hasn't my bench improved?", _ctx(_bench_history()), llm=llm)
    assert result.generation.source == "fallback"
    assert result.generation.fallback_reason == "ungrounded"
    assert result.grounded is True
    assert any(item["name"] == "get_exercise_history" for item in result.tool_calls)
    assert "try harder" not in result.answer.lower()


def test_coach_http_uses_logged_sets() -> None:
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
    workout = client.post(f"/v1/users/{user_id}/workouts", json={"day_index": 0})
    workout_id = workout.json()["id"]
    for week, weight in enumerate((32.0, 28.0, 24.0)):
        client.post(
            f"/v1/workouts/{workout_id}/sets",
            json={
                "exercise_id": "db_bench_press",
                "set_index": week,
                "weight_kg": weight,
                "reps": 8,
                "rpe": 9,
                "rir": 0,
            },
        )
    response = client.post(
        f"/v1/users/{user_id}/coach",
        json={"message": "Why hasn't my bench improved?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is True
    names = [item["name"] for item in body["tool_calls"]]
    assert "get_exercise_history" in names
    assert "get_muscle_volume" in names
    assert body["generation"]["prompt_version"] == CURRENT_COACH_PROMPT
    assert "bench" in body["answer"].lower() or "db_bench" in str(body["tool_calls"]).lower()
    assert "just try harder" not in body["answer"].lower()
