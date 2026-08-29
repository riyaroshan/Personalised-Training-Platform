from __future__ import annotations

from app.engine.catalog import Catalog
from app.engine.duration import estimate_minutes
from app.engine.progression import apply_progression
from app.engine.splits import DayTemplate, Slot, select_split
from app.engine.types import (
    Equipment,
    Exercise,
    ExercisePrescription,
    Goal,
    Muscle,
    TrainingAge,
    UserConstraints,
    WorkoutPlan,
    WorkoutPlanDay,
    WorkoutSetLog,
)
from app.engine.validate import validate_plan


def generate_plan(
    constraints: UserConstraints,
    catalog: Catalog,
    history: list[WorkoutSetLog] | None = None,
    sessions_completed: int = 0,
) -> WorkoutPlan:
    split_name, templates = select_split(constraints.days_per_week, constraints.training_age)
    eligible = catalog.eligible(constraints)
    used_ids: set[str] = set()
    days: list[WorkoutPlanDay] = []

    for index, template in enumerate(templates):
        prescriptions = _fill_day(template, eligible, used_ids, constraints)
        prescriptions = _fit_duration(prescriptions, constraints, catalog)
        days.append(
            WorkoutPlanDay(
                day_index=index,
                label=template.label,
                focus=template.focus,
                estimated_minutes=estimate_minutes(prescriptions, catalog),
                exercises=prescriptions,
            )
        )

    days = _ensure_coverage(days, constraints, catalog, eligible)
    reasoning = _reasoning(constraints, split_name, days)
    plan = WorkoutPlan(
        days_per_week=constraints.days_per_week,
        split=split_name,
        days=days,
        reasoning=reasoning,
    )
    plan = apply_progression(
        plan,
        history or [],
        catalog,
        sessions_completed=sessions_completed,
        days_per_week=constraints.days_per_week,
    )
    for day in plan.days:
        day.estimated_minutes = estimate_minutes(day.exercises, catalog)
    return plan


def _fill_day(
    template: DayTemplate,
    eligible: list[Exercise],
    used_ids: set[str],
    constraints: UserConstraints,
) -> list[ExercisePrescription]:
    used_groups: set[str] = set()
    prescriptions: list[ExercisePrescription] = []
    for slot in template.slots:
        exercise = _pick(slot, eligible, used_ids, used_groups, constraints)
        if exercise is None:
            continue
        prescriptions.append(_prescribe(exercise, constraints, optional=slot.optional))
        used_ids.add(exercise.id)
        used_groups.add(exercise.substitution_group)
    return prescriptions


def _pick(
    slot: Slot,
    eligible: list[Exercise],
    used_ids: set[str],
    used_groups: set[str],
    constraints: UserConstraints,
    *,
    require_compound: bool | None = None,
    max_difficulty: int | None = None,
) -> Exercise | None:
    require_compound = slot.require_compound if require_compound is None else require_compound
    max_difficulty = _max_difficulty(constraints.training_age) if max_difficulty is None else max_difficulty
    ranked: list[tuple[int, str, Exercise]] = []
    for exercise in eligible:
        if exercise.id in used_ids:
            continue
        if exercise.movement_pattern != slot.pattern:
            continue
        if require_compound and not exercise.is_compound:
            continue
        if exercise.difficulty > max_difficulty:
            continue
        score = exercise.difficulty
        score += _equipment_penalty(exercise, constraints)
        if slot.primary and slot.primary not in exercise.primary_muscles:
            score += 2
        if exercise.substitution_group in used_groups:
            score += 4
        if slot.primary and slot.primary in exercise.primary_muscles:
            score -= 1
        ranked.append((score, exercise.name, exercise))
    if ranked:
        ranked.sort()
        return ranked[0][2]
    if require_compound:
        return _pick(
            slot,
            eligible,
            used_ids,
            used_groups,
            constraints,
            require_compound=False,
            max_difficulty=max_difficulty,
        )
    if max_difficulty < 5:
        return _pick(
            slot,
            eligible,
            used_ids,
            used_groups,
            constraints,
            require_compound=False,
            max_difficulty=5,
        )
    return None


def _equipment_penalty(exercise: Exercise, constraints: UserConstraints) -> int:
    gym = {
        Equipment.BARBELL,
        Equipment.DUMBBELL,
        Equipment.CABLE,
        Equipment.MACHINE,
        Equipment.KETTLEBELL,
        Equipment.SMITH,
        Equipment.EZ_BAR,
        Equipment.TRAP_BAR,
    }
    if not gym.intersection(constraints.available_equipment):
        return 0
    if set(exercise.equipment).issubset({Equipment.BODYWEIGHT, Equipment.BAND}):
        return 5
    return 0


def _max_difficulty(training_age: TrainingAge) -> int:
    if training_age == TrainingAge.BEGINNER:
        return 3
    if training_age == TrainingAge.INTERMEDIATE:
        return 4
    return 5


def _prescribe(exercise: Exercise, constraints: UserConstraints, *, optional: bool) -> ExercisePrescription:
    sets = 2 if optional and constraints.training_age == TrainingAge.BEGINNER else 3
    if constraints.training_age == TrainingAge.ADVANCED and not optional:
        sets = 4
    if constraints.goal == Goal.STRENGTH:
        rep_min, rep_max = (4, 6) if exercise.is_compound else (6, 10)
        rir = 1
    elif constraints.goal == Goal.HYPERTROPHY:
        rep_min, rep_max = (8, 12) if exercise.is_compound else (10, 15)
        rir = 2
    else:
        rep_min, rep_max = (8, 12)
        rir = 2
    return ExercisePrescription(
        exercise_id=exercise.id,
        sets=sets,
        rep_min=rep_min,
        rep_max=rep_max,
        target_rir=rir,
        rest_seconds=exercise.rest_seconds,
    )


def _fit_duration(
    prescriptions: list[ExercisePrescription],
    constraints: UserConstraints,
    catalog: Catalog,
) -> list[ExercisePrescription]:
    fitted = list(prescriptions)
    while (
        estimate_minutes(fitted, catalog) > constraints.max_duration_minutes
        and len(fitted) > 3
    ):
        dropped = False
        for index in range(len(fitted) - 1, 2, -1):
            if not catalog.get(fitted[index].exercise_id).is_compound:
                fitted.pop(index)
                dropped = True
                break
        if not dropped:
            break

    def shrink() -> bool:
        for index, prescription in enumerate(fitted):
            if prescription.rest_seconds > 60:
                fitted[index] = prescription.model_copy(
                    update={"rest_seconds": prescription.rest_seconds - 15}
                )
                return True
        for index in range(len(fitted) - 1, -1, -1):
            if fitted[index].sets > 2:
                fitted[index] = fitted[index].model_copy(update={"sets": fitted[index].sets - 1})
                return True
        return False

    while estimate_minutes(fitted, catalog) > constraints.max_duration_minutes:
        if not shrink():
            break
    return fitted


def _ensure_coverage(
    days: list[WorkoutPlanDay],
    constraints: UserConstraints,
    catalog: Catalog,
    eligible: list[Exercise],
) -> list[WorkoutPlanDay]:
    probe = WorkoutPlan(days_per_week=len(days), split="probe", days=days, reasoning="")
    missing = {
        violation.message
        for violation in validate_plan(probe, constraints, catalog)
        if violation.code == "coverage"
    }
    if not missing:
        return days

    used = {prescription.exercise_id for day in days for prescription in day.exercises}
    needed_muscles = [Muscle.QUADS, Muscle.GLUTES, Muscle.CHEST, Muscle.LATS, Muscle.SHOULDERS]
    updated = [day.model_copy(update={"exercises": list(day.exercises)}) for day in days]
    for muscle in needed_muscles:
        candidate = next(
            (
                exercise
                for exercise in eligible
                if muscle in exercise.primary_muscles and exercise.id not in used
            ),
            None,
        )
        if candidate is None:
            continue
        shortest = min(range(len(updated)), key=lambda i: updated[i].estimated_minutes)
        trial = list(updated[shortest].exercises) + [_prescribe(candidate, constraints, optional=True)]
        if estimate_minutes(trial, catalog) > constraints.max_duration_minutes:
            trial = _fit_duration(trial, constraints, catalog)
        used.add(candidate.id)
        updated[shortest] = updated[shortest].model_copy(
            update={
                "exercises": trial,
                "estimated_minutes": estimate_minutes(trial, catalog),
            }
        )
    return updated


def _reasoning(
    constraints: UserConstraints,
    split_name: str,
    days: list[WorkoutPlanDay],
) -> str:
    labels = ", ".join(day.label for day in days)
    equipment = ", ".join(item.value for item in constraints.available_equipment)
    return (
        f"{constraints.training_age.value} {constraints.goal.value} program using a {split_name} split "
        f"({labels}). Sessions capped at {constraints.max_duration_minutes} minutes. "
        f"Equipment: {equipment or 'none'}."
    )
