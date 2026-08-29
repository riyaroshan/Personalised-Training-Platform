from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.progression import apply_progression
from app.engine.substitutions import find_substitutes
from app.engine.types import (
    Equipment,
    Goal,
    TrainingAge,
    UserConstraints,
    WorkoutSetLog,
)
from app.engine.validate import validate_plan


def beginner_no_barbell() -> UserConstraints:
    return UserConstraints(
        days_per_week=3,
        max_duration_minutes=45,
        available_equipment=[
            Equipment.DUMBBELL,
            Equipment.CABLE,
            Equipment.MACHINE,
            Equipment.BODYWEIGHT,
            Equipment.KETTLEBELL,
            Equipment.BAND,
        ],
        injuries=[],
        goal=Goal.HYPERTROPHY,
        training_age=TrainingAge.BEGINNER,
    )


def test_beginner_hypertrophy_constraints() -> None:
    constraints = beginner_no_barbell()
    plan = generate_plan(constraints, CATALOG)
    violations = validate_plan(plan, constraints, CATALOG)
    assert violations == [], [item.model_dump() for item in violations]
    assert len(plan.days) == 3
    assert all(day.estimated_minutes <= 45 for day in plan.days)
    ids = [p.exercise_id for day in plan.days for p in day.exercises]
    assert all(exercise_id in CATALOG.by_id for exercise_id in ids)
    for exercise_id in ids:
        assert Equipment.BARBELL not in CATALOG.get(exercise_id).equipment


def test_exact_day_count_and_valid_exercises() -> None:
    for days in (2, 3, 4, 5, 6):
        constraints = beginner_no_barbell().model_copy(update={"days_per_week": days})
        plan = generate_plan(constraints, CATALOG)
        assert len(plan.days) == days
        assert validate_plan(plan, constraints, CATALOG) == []


def test_barbell_allowed_can_include_barbell() -> None:
    constraints = beginner_no_barbell().model_copy(
        update={"available_equipment": list(Equipment)}
    )
    plan = generate_plan(constraints, CATALOG)
    assert validate_plan(plan, constraints, CATALOG) == []


def test_knee_injury_avoids_contraindicated_squats() -> None:
    constraints = beginner_no_barbell().model_copy(update={"injuries": ["knee"]})
    plan = generate_plan(constraints, CATALOG)
    violations = validate_plan(plan, constraints, CATALOG)
    assert all(item.code != "injury" for item in violations)
    for day in plan.days:
        for prescription in day.exercises:
            exercise = CATALOG.get(prescription.exercise_id)
            assert "knee" not in exercise.contraindications


def test_cable_fly_substitutes_prefer_same_pattern() -> None:
    matches = find_substitutes("cable_fly", beginner_no_barbell(), CATALOG)
    assert matches
    assert matches[0][0].substitution_group == "fly"
    assert all(Equipment.BARBELL not in exercise.equipment for exercise, _ in matches)


def test_progression_adds_weight_after_hitting_rep_max() -> None:
    from datetime import datetime, timezone

    constraints = beginner_no_barbell()
    plan = generate_plan(constraints, CATALOG)
    first = plan.days[0].exercises[0]
    history = [
        WorkoutSetLog(
            exercise_id=first.exercise_id,
            weight_kg=20,
            reps=first.rep_max,
            rpe=7,
            rir=2,
            completed_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
            set_index=index,
        )
        for index in range(first.sets)
    ]
    progressed = apply_progression(plan, history, CATALOG)
    updated = progressed.days[0].exercises[0]
    increment = CATALOG.get(first.exercise_id).increment_kg
    assert updated.target_weight_kg == 20 + increment
