from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from app.engine.catalog import Catalog
from app.engine.types import ExercisePrescription, WorkoutPlan, WorkoutSetLog


def apply_progression(
    plan: WorkoutPlan,
    history: list[WorkoutSetLog],
    catalog: Catalog,
    *,
    sessions_completed: int = 0,
    days_per_week: int = 3,
) -> WorkoutPlan:
    last_sessions = _last_sessions(history)
    deload = _is_deload_week(sessions_completed, days_per_week)
    updated_days = []
    for day in plan.days:
        exercises = [
            _progress_prescription(prescription, last_sessions, catalog, deload)
            for prescription in day.exercises
        ]
        updated_days.append(day.model_copy(update={"exercises": exercises}))
    reasoning = plan.reasoning
    if deload:
        reasoning = f"{reasoning} Deload week: volume and load reduced."
    return plan.model_copy(update={"days": updated_days, "reasoning": reasoning})


def _is_deload_week(sessions_completed: int, days_per_week: int) -> bool:
    if sessions_completed <= 0 or days_per_week <= 0:
        return False
    week = sessions_completed // days_per_week
    return week > 0 and week % 5 == 0


def _last_sessions(history: list[WorkoutSetLog]) -> dict[str, list[WorkoutSetLog]]:
    by_exercise: dict[str, list[WorkoutSetLog]] = defaultdict(list)
    for entry in sorted(history, key=lambda item: item.completed_at):
        by_exercise[entry.exercise_id].append(entry)
    latest: dict[str, list[WorkoutSetLog]] = {}
    for exercise_id, entries in by_exercise.items():
        last_stamp = entries[-1].completed_at
        session_date = last_stamp.date() if isinstance(last_stamp, datetime) else last_stamp
        latest[exercise_id] = [
            entry
            for entry in entries
            if (entry.completed_at.date() if isinstance(entry.completed_at, datetime) else entry.completed_at)
            == session_date
        ]
    return latest


def _progress_prescription(
    prescription: ExercisePrescription,
    last_sessions: dict[str, list[WorkoutSetLog]],
    catalog: Catalog,
    deload: bool,
) -> ExercisePrescription:
    exercise = catalog.get(prescription.exercise_id)
    last = last_sessions.get(prescription.exercise_id, [])
    weight = prescription.target_weight_kg
    sets = prescription.sets

    if last:
        logged_weights = [entry.weight_kg for entry in last if entry.weight_kg is not None]
        weight = logged_weights[-1] if logged_weights else weight
        hit_top = bool(last) and all(entry.reps >= prescription.rep_max for entry in last)
        missed_floor = any(entry.reps < prescription.rep_min for entry in last)
        if weight is not None and hit_top:
            weight = round(weight + exercise.increment_kg, 2)
        elif weight is not None and missed_floor:
            previous_fail = _consecutive_failures(last_sessions, prescription)
            if previous_fail >= 2:
                weight = round(weight * 0.9, 2)

    if deload:
        sets = max(2, round(sets * 0.6))
        if weight is not None:
            weight = round(weight * 0.9, 2)

    return prescription.model_copy(update={"target_weight_kg": weight, "sets": sets})


def _consecutive_failures(
    last_sessions: dict[str, list[WorkoutSetLog]],
    prescription: ExercisePrescription,
) -> int:
    session = last_sessions.get(prescription.exercise_id, [])
    if not session:
        return 0
    return 1 if any(entry.reps < prescription.rep_min for entry in session) else 0
