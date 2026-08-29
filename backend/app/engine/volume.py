from __future__ import annotations

from collections import defaultdict

from app.engine.catalog import Catalog
from app.engine.types import Muscle, WorkoutPlan


def weekly_sets_by_muscle(plan: WorkoutPlan, catalog: Catalog) -> dict[Muscle, int]:
    volume: dict[Muscle, int] = defaultdict(int)
    for day in plan.days:
        for prescription in day.exercises:
            exercise = catalog.get(prescription.exercise_id)
            for muscle in exercise.primary_muscles:
                volume[muscle] += prescription.sets
            for muscle in exercise.secondary_muscles:
                volume[muscle] += max(1, prescription.sets // 2)
    return dict(volume)
