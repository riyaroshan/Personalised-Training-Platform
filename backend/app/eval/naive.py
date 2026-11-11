from __future__ import annotations

from app.engine.catalog import Catalog
from app.engine.types import ExercisePrescription, UserConstraints, WorkoutPlan, WorkoutPlanDay


def naive_plan(constraints: UserConstraints, catalog: Catalog) -> WorkoutPlan:
    """Ignores equipment, duration, and injuries — a baseline the engine should beat."""
    picks = catalog.exercises[:6]
    days = []
    for index in range(constraints.days_per_week):
        days.append(
            WorkoutPlanDay(
                day_index=index,
                label=f"Naive {index + 1}",
                focus="everything",
                estimated_minutes=constraints.max_duration_minutes + 40,
                exercises=[
                    ExercisePrescription(
                        exercise_id=exercise.id,
                        sets=4,
                        rep_min=8,
                        rep_max=12,
                        target_rir=0,
                    )
                    for exercise in picks
                ],
            )
        )
    return WorkoutPlan(
        days_per_week=constraints.days_per_week,
        split="naive",
        days=days,
        reasoning="Pick the first catalog entries and overflow the time cap.",
    )
