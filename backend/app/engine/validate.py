from __future__ import annotations

from pydantic import BaseModel

from app.engine.catalog import Catalog
from app.engine.types import (
    Equipment,
    Muscle,
    UserConstraints,
    WorkoutPlan,
)


class PlanViolation(BaseModel):
    code: str
    message: str


def validate_plan(
    plan: WorkoutPlan,
    constraints: UserConstraints,
    catalog: Catalog,
) -> list[PlanViolation]:
    violations: list[PlanViolation] = []
    if len(plan.days) != constraints.days_per_week:
        violations.append(
            PlanViolation(
                code="days_per_week",
                message=f"Expected {constraints.days_per_week} days, got {len(plan.days)}",
            )
        )

    allowed = set(constraints.available_equipment)
    injuries = set(constraints.injuries)
    seen_ids: set[str] = set()

    for day in plan.days:
        if day.estimated_minutes > constraints.max_duration_minutes:
            violations.append(
                PlanViolation(
                    code="duration",
                    message=(
                        f"{day.label} estimated {day.estimated_minutes} min "
                        f"> {constraints.max_duration_minutes} min cap"
                    ),
                )
            )
        if not day.exercises:
            violations.append(PlanViolation(code="empty_day", message=f"{day.label} has no exercises"))
        for prescription in day.exercises:
            if prescription.exercise_id not in catalog.by_id:
                violations.append(
                    PlanViolation(
                        code="unknown_exercise",
                        message=f"Unknown exercise {prescription.exercise_id}",
                    )
                )
                continue
            exercise = catalog.get(prescription.exercise_id)
            seen_ids.add(exercise.id)
            if not set(exercise.equipment).issubset(allowed):
                violations.append(
                    PlanViolation(
                        code="equipment",
                        message=f"{exercise.name} needs {[e.value for e in exercise.equipment]}",
                    )
                )
            if Equipment.BARBELL in exercise.equipment and Equipment.BARBELL not in allowed:
                violations.append(
                    PlanViolation(code="no_barbell", message=f"{exercise.name} is a barbell lift")
                )
            if injuries.intersection(exercise.contraindications):
                violations.append(
                    PlanViolation(
                        code="injury",
                        message=f"{exercise.name} contraindicated for {constraints.injuries}",
                    )
                )
            if prescription.rep_max < prescription.rep_min:
                violations.append(
                    PlanViolation(
                        code="rep_range",
                        message=f"{exercise.name} has invalid rep range",
                    )
                )

    missing = _missing_coverage(plan, catalog, constraints)
    if missing:
        violations.append(
            PlanViolation(
                code="coverage",
                message=f"Missing major muscle coverage: {sorted(m.value for m in missing)}",
            )
        )
    return violations


def _hit_muscles(plan: WorkoutPlan, catalog: Catalog) -> set[Muscle]:
    hit: set[Muscle] = set()
    for day in plan.days:
        for prescription in day.exercises:
            if prescription.exercise_id not in catalog.by_id:
                continue
            exercise = catalog.get(prescription.exercise_id)
            hit.update(exercise.primary_muscles)
            hit.update(exercise.secondary_muscles)
    return hit


def _missing_coverage(
    plan: WorkoutPlan, catalog: Catalog, constraints: UserConstraints
) -> set[Muscle]:
    hit = _hit_muscles(plan, catalog)
    required_groups = [
        {Muscle.QUADS},
        {Muscle.HAMSTRINGS, Muscle.GLUTES},
        {Muscle.CHEST},
        {Muscle.LATS, Muscle.UPPER_BACK},
        {Muscle.SHOULDERS, Muscle.CHEST},
    ]
    injuries = set(constraints.injuries)
    if "knee" in injuries:
        required_groups = [group for group in required_groups if Muscle.QUADS not in group]
    if "shoulder" in injuries:
        required_groups = [group for group in required_groups if Muscle.SHOULDERS not in group]
    missing: set[Muscle] = set()
    for group in required_groups:
        if hit.isdisjoint(group):
            missing.add(next(iter(group)))
    return missing
