from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.engine.catalog import CATALOG
from app.engine.generator import generate_plan
from app.engine.substitutions import find_substitutes
from app.engine.types import Equipment, Goal, TrainingAge, UserConstraints, WorkoutPlan, WorkoutSetLog
from app.engine.validate import validate_plan
from app.models import LoggedSet, User, Workout
from app.ai.client import StructuredLLM
from app.ai.orchestrator import AIPlanResult, generate_ai_plan


def constraints_from_user(user: User) -> UserConstraints:
    return UserConstraints(
        days_per_week=user.days_per_week,
        max_duration_minutes=user.max_duration_minutes,
        available_equipment=[Equipment(item) for item in user.available_equipment],
        injuries=user.injuries or [],
        goal=Goal(user.goal),
        training_age=TrainingAge(user.training_age),
        excluded_exercise_ids=user.excluded_exercise_ids or [],
    )


def history_for_user(db: Session, user_id: str) -> list[WorkoutSetLog]:
    rows = (
        db.query(LoggedSet)
        .join(Workout)
        .filter(Workout.user_id == user_id)
        .order_by(LoggedSet.completed_at.asc())
        .all()
    )
    return [
        WorkoutSetLog(
            exercise_id=row.exercise_id,
            weight_kg=row.weight_kg,
            reps=row.reps,
            rpe=row.rpe,
            rir=row.rir,
            completed_at=row.completed_at,
            set_index=row.set_index,
        )
        for row in rows
    ]


def generate_and_store_plan(db: Session, user: User) -> WorkoutPlan:
    plan = generate_plan(
        constraints_from_user(user),
        CATALOG,
        history=history_for_user(db, user.id),
        sessions_completed=user.sessions_completed,
    )
    user.current_plan = plan.model_dump(mode="json")
    db.add(user)
    db.commit()
    db.refresh(user)
    return plan


def generate_ai_and_store_plan(
    db: Session,
    user: User,
    llm: StructuredLLM | None = None,
) -> AIPlanResult:
    result = generate_ai_plan(
        constraints_from_user(user),
        CATALOG,
        history=history_for_user(db, user.id),
        sessions_completed=user.sessions_completed,
        llm=llm,
    )
    user.current_plan = result.plan.model_dump(mode="json")
    db.add(user)
    db.commit()
    db.refresh(user)
    return result


def plan_violations(user: User, plan: WorkoutPlan) -> list[str]:
    return [
        f"{item.code}: {item.message}"
        for item in validate_plan(plan, constraints_from_user(user), CATALOG)
    ]


def substitutes_for(exercise_id: str, user: User, limit: int = 5):
    return find_substitutes(exercise_id, constraints_from_user(user), CATALOG, limit=limit)


def start_workout(db: Session, user: User, day_index: int) -> Workout:
    if not user.current_plan:
        generate_and_store_plan(db, user)
    plan = WorkoutPlan.model_validate(user.current_plan)
    if day_index >= len(plan.days):
        raise ValueError(f"day_index {day_index} is out of range for this plan")
    day = plan.days[day_index]
    workout = Workout(user_id=user.id, day_index=day_index, label=day.label)
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def complete_workout(db: Session, workout: Workout) -> Workout:
    if workout.completed_at is None:
        user = db.get(User, workout.user_id)
        workout.completed_at = datetime.now(UTC)
        if user is not None:
            user.sessions_completed += 1
            db.add(user)
        db.add(workout)
        db.commit()
        db.refresh(workout)
    return workout
