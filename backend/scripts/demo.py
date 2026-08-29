from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.types import Equipment, Goal, TrainingAge, UserConstraints
from app.engine.validate import validate_plan


def main() -> None:
    constraints = UserConstraints(
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
        goal=Goal.HYPERTROPHY,
        training_age=TrainingAge.BEGINNER,
    )
    plan = generate_plan(constraints, CATALOG)
    violations = validate_plan(plan, constraints, CATALOG)
    print(plan.split)
    print(plan.reasoning)
    print()
    for day in plan.days:
        print(f"{day.label}  ({day.estimated_minutes} min)")
        for prescription in day.exercises:
            exercise = CATALOG.get(prescription.exercise_id)
            print(
                f"  {exercise.name:28} {prescription.sets} x "
                f"{prescription.rep_min}-{prescription.rep_max}  "
                f"RIR {prescription.target_rir}"
            )
        print()
    if violations:
        print("VIOLATIONS")
        for item in violations:
            print(f"  {item.code}: {item.message}")
    else:
        print("Plan satisfies constraints.")


if __name__ == "__main__":
    main()
