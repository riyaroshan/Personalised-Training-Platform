from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from app.engine.catalog import Catalog
from app.engine.types import Muscle, WorkoutPlan, WorkoutSetLog


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


def logged_sets_by_muscle(
    history: list[WorkoutSetLog],
    catalog: Catalog,
    *,
    days: int = 30,
    now: datetime | None = None,
) -> dict[Muscle, int]:
    cutoff = _cutoff(days, now)
    volume: dict[Muscle, int] = defaultdict(int)
    seen: set[tuple[str, int, str]] = set()
    for entry in history:
        if _aware(entry.completed_at) < cutoff:
            continue
        exercise = catalog.get(entry.exercise_id)
        key = (entry.exercise_id, entry.set_index, entry.completed_at.isoformat())
        if key in seen:
            continue
        seen.add(key)
        for muscle in exercise.primary_muscles:
            volume[muscle] += 1
        for muscle in exercise.secondary_muscles:
            volume[muscle] += 0
    return dict(volume)


def _cutoff(days: int, now: datetime | None) -> datetime:
    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp - timedelta(days=days)


def _aware(stamp: datetime) -> datetime:
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=UTC)
    return stamp
