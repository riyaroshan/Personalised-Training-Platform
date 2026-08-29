from __future__ import annotations

from dataclasses import dataclass

from app.engine.catalog import Catalog
from app.engine.types import UserConstraints, WorkoutSetLog


CURRENT_WORKOUT_PLAN_PROMPT = "workout_plan.v1"


@dataclass(frozen=True)
class PromptVersion:
    id: str
    task: str
    system: str


PROMPTS: dict[str, PromptVersion] = {
    "workout_plan.v1": PromptVersion(
        id="workout_plan.v1",
        task="workout_plan",
        system=(
            "You are a programming engine for a strength-training app. "
            "Return only a structured workout plan that matches the schema. "
            "Rules:\n"
            "- Use ONLY exercise_id values from the provided catalog. Never invent ids.\n"
            "- days must contain exactly the requested days_per_week entries.\n"
            "- Each day must fit in max_duration_minutes. Prefer 4–6 exercises, 2–3 sets.\n"
            "- Cover quads, a hinge (hamstrings/glutes), chest, and back across the week.\n"
            "- Respect injuries: do not pick contraindicated movements.\n"
            "- Hypertrophy: compounds 8–12 reps, isolation 10–15, RIR 2.\n"
            "- Strength: compounds 4–6 reps, RIR 1.\n"
            "- reasoning should cite constraints, not generic motivation.\n"
            "If a previous attempt is attached, it failed validation — fix every listed error."
        ),
    )
}


def get_prompt(version_id: str | None = None) -> PromptVersion:
    key = version_id or CURRENT_WORKOUT_PLAN_PROMPT
    try:
        return PROMPTS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown prompt version: {key}") from exc


def render_user_prompt(
    constraints: UserConstraints,
    catalog: Catalog,
    history: list[WorkoutSetLog],
) -> str:
    eligible = catalog.eligible(constraints)
    exercises = [
        {
            "id": exercise.id,
            "name": exercise.name,
            "pattern": exercise.movement_pattern.value,
            "primary": [muscle.value for muscle in exercise.primary_muscles],
            "equipment": [item.value for item in exercise.equipment],
            "compound": exercise.is_compound,
            "contraindications": exercise.contraindications,
        }
        for exercise in eligible
    ]
    recent = [
        {
            "exercise_id": entry.exercise_id,
            "weight_kg": entry.weight_kg,
            "reps": entry.reps,
            "rir": entry.rir,
            "completed_at": entry.completed_at.isoformat(),
        }
        for entry in history[-30:]
    ]
    return (
        "Generate a week of training for this athlete.\n\n"
        f"days_per_week: {constraints.days_per_week}\n"
        f"max_duration_minutes: {constraints.max_duration_minutes}\n"
        f"goal: {constraints.goal.value}\n"
        f"training_age: {constraints.training_age.value}\n"
        f"injuries: {constraints.injuries or []}\n"
        f"equipment: {[item.value for item in constraints.available_equipment]}\n"
        f"excluded_exercise_ids: {constraints.excluded_exercise_ids}\n\n"
        f"catalog ({len(exercises)} eligible exercises):\n{exercises}\n\n"
        f"recent_history ({len(recent)} sets):\n{recent or 'none'}\n"
    )
