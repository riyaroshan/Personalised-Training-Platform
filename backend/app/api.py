from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.ai.client import StructuredLLM, build_llm
from app.ai.schemas import GenerationMeta
from app.db import get_db
from app.engine.catalog import CATALOG
from app.engine.types import UserConstraints, WorkoutPlan
from app.models import LoggedSet, User, Workout
from app.rag.answer import RagAnswer, ablate, answer_question
from app.rag.exercises import compare_substitutes, similar_exercises
from app.rag.index import get_index
from app.rag.retrieve import RetrieverConfig
from app.schemas import (
    ExercisePublic,
    LoggedSetPublic,
    PlanResponse,
    RagQuery,
    SetLogCreate,
    SimilarQuery,
    SubstitutePublic,
    UserCreate,
    UserPublic,
    WorkoutPublic,
    WorkoutStart,
)
from app.services import (
    complete_workout,
    generate_ai_and_store_plan,
    generate_and_store_plan,
    plan_violations,
    start_workout,
    substitutes_for,
)

router = APIRouter()


def get_structured_llm() -> StructuredLLM | None:
    return build_llm()


def _user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _to_user_public(user: User) -> UserPublic:
    plan = WorkoutPlan.model_validate(user.current_plan) if user.current_plan else None
    return UserPublic(
        id=user.id,
        name=user.name,
        days_per_week=user.days_per_week,
        max_duration_minutes=user.max_duration_minutes,
        available_equipment=user.available_equipment,
        injuries=user.injuries or [],
        goal=user.goal,
        training_age=user.training_age,
        sessions_completed=user.sessions_completed,
        current_plan=plan,
    )


def _exercise_public(exercise) -> ExercisePublic:
    return ExercisePublic(
        id=exercise.id,
        name=exercise.name,
        movement_pattern=exercise.movement_pattern.value,
        primary_muscles=[item.value for item in exercise.primary_muscles],
        secondary_muscles=[item.value for item in exercise.secondary_muscles],
        equipment=[item.value for item in exercise.equipment],
        difficulty=exercise.difficulty,
        is_compound=exercise.is_compound,
        substitution_group=exercise.substitution_group,
    )


def _workout_public(workout: Workout) -> WorkoutPublic:
    return WorkoutPublic(
        id=workout.id,
        user_id=workout.user_id,
        day_index=workout.day_index,
        label=workout.label,
        started_at=workout.started_at,
        completed_at=workout.completed_at,
        sets=[
            LoggedSetPublic(
                id=row.id,
                exercise_id=row.exercise_id,
                set_index=row.set_index,
                weight_kg=row.weight_kg,
                reps=row.reps,
                rpe=row.rpe,
                rir=row.rir,
                completed_at=row.completed_at,
            )
            for row in workout.sets
        ],
    )


@router.post("/users", response_model=UserPublic)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserPublic:
    user = User(
        name=payload.name,
        days_per_week=payload.days_per_week,
        max_duration_minutes=payload.max_duration_minutes,
        available_equipment=[item.value for item in payload.available_equipment],
        injuries=payload.injuries,
        goal=payload.goal.value,
        training_age=payload.training_age.value,
        excluded_exercise_ids=payload.excluded_exercise_ids,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_public(user)


@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserPublic:
    return _to_user_public(_user_or_404(db, user_id))


@router.post("/users/{user_id}/plan", response_model=PlanResponse)
def create_plan(user_id: str, db: Session = Depends(get_db)) -> PlanResponse:
    user = _user_or_404(db, user_id)
    plan = generate_and_store_plan(db, user)
    return PlanResponse(
        user_id=user.id,
        plan=plan,
        violations=plan_violations(user, plan),
        generation=GenerationMeta(source="engine", attempts=1),
    )


@router.post("/users/{user_id}/plan/ai", response_model=PlanResponse)
def create_ai_plan(
    user_id: str,
    db: Session = Depends(get_db),
    llm: StructuredLLM | None = Depends(get_structured_llm),
) -> PlanResponse:
    user = _user_or_404(db, user_id)
    result = generate_ai_and_store_plan(db, user, llm=llm)
    return PlanResponse(
        user_id=user.id,
        plan=result.plan,
        violations=plan_violations(user, result.plan),
        generation=result.generation,
    )


@router.get("/users/{user_id}/plan", response_model=PlanResponse)
def get_plan(user_id: str, db: Session = Depends(get_db)) -> PlanResponse:
    user = _user_or_404(db, user_id)
    if not user.current_plan:
        plan = generate_and_store_plan(db, user)
        generation = GenerationMeta(source="engine", attempts=1)
    else:
        plan = WorkoutPlan.model_validate(user.current_plan)
        generation = None
    return PlanResponse(
        user_id=user.id,
        plan=plan,
        violations=plan_violations(user, plan),
        generation=generation,
    )


@router.get("/exercises", response_model=list[ExercisePublic])
def list_exercises() -> list[ExercisePublic]:
    return [_exercise_public(exercise) for exercise in CATALOG.exercises]


@router.get("/exercises/{exercise_id}/substitutes", response_model=list[SubstitutePublic])
def list_substitutes(
    exercise_id: str,
    user_id: str,
    db: Session = Depends(get_db),
) -> list[SubstitutePublic]:
    if exercise_id not in CATALOG.by_id:
        raise HTTPException(status_code=404, detail="Exercise not found")
    user = _user_or_404(db, user_id)
    return [
        SubstitutePublic(exercise=_exercise_public(exercise), score=score)
        for exercise, score in substitutes_for(exercise_id, user)
    ]


@router.post("/users/{user_id}/workouts", response_model=WorkoutPublic)
def create_workout(user_id: str, payload: WorkoutStart, db: Session = Depends(get_db)) -> WorkoutPublic:
    user = _user_or_404(db, user_id)
    try:
        workout = start_workout(db, user, payload.day_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    loaded = (
        db.query(Workout)
        .options(selectinload(Workout.sets))
        .filter(Workout.id == workout.id)
        .one()
    )
    return _workout_public(loaded)


@router.post("/workouts/{workout_id}/sets", response_model=LoggedSetPublic)
def log_set(workout_id: str, payload: SetLogCreate, db: Session = Depends(get_db)) -> LoggedSetPublic:
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    if payload.exercise_id not in CATALOG.by_id:
        raise HTTPException(status_code=400, detail="Unknown exercise_id")
    row = LoggedSet(
        workout_id=workout.id,
        exercise_id=payload.exercise_id,
        set_index=payload.set_index,
        weight_kg=payload.weight_kg,
        reps=payload.reps,
        rpe=payload.rpe,
        rir=payload.rir,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LoggedSetPublic(
        id=row.id,
        exercise_id=row.exercise_id,
        set_index=row.set_index,
        weight_kg=row.weight_kg,
        reps=row.reps,
        rpe=row.rpe,
        rir=row.rir,
        completed_at=row.completed_at,
    )


@router.post("/workouts/{workout_id}/complete", response_model=WorkoutPublic)
def finish_workout(workout_id: str, db: Session = Depends(get_db)) -> WorkoutPublic:
    workout = db.query(Workout).options(selectinload(Workout.sets)).filter(Workout.id == workout_id).first()
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return _workout_public(complete_workout(db, workout))


@router.get("/users/{user_id}/history", response_model=list[WorkoutPublic])
def workout_history(user_id: str, db: Session = Depends(get_db)) -> list[WorkoutPublic]:
    _user_or_404(db, user_id)
    workouts = (
        db.query(Workout)
        .options(selectinload(Workout.sets))
        .filter(Workout.user_id == user_id)
        .order_by(Workout.started_at.desc())
        .all()
    )
    return [_workout_public(item) for item in workouts]


@router.post("/rag/query", response_model=RagAnswer)
def rag_query(payload: RagQuery) -> RagAnswer:
    config = RetrieverConfig(
        top_k=payload.top_k,
        hybrid=payload.hybrid,
        rerank=payload.rerank,
        contextual=payload.contextual,
        topic=payload.topic,
        chunk_size=get_index().config.chunk_size,
        overlap=get_index().config.overlap,
    )
    return answer_question(payload.question, config=config)


@router.get("/rag/ablate")
def rag_ablate(question: str = "Should I train chest twice or three times a week?") -> list[dict]:
    return ablate(question)


@router.post("/exercises/similar")
def embedding_similar(payload: SimilarQuery) -> dict:
    if payload.exercise_id not in CATALOG.by_id:
        raise HTTPException(status_code=404, detail="Exercise not found")
    constraints = UserConstraints(
        days_per_week=3,
        max_duration_minutes=45,
        available_equipment=payload.available_equipment,
        injuries=payload.injuries,
    )
    embeddings = similar_exercises(payload.exercise_id, constraints, limit=payload.limit)
    return {
        "exercise_id": payload.exercise_id,
        "matches": [
            {
                "exercise_id": exercise.id,
                "name": exercise.name,
                "score": score,
                "equipment": [item.value for item in exercise.equipment],
                "substitution_group": exercise.substitution_group,
            }
            for exercise, score in embeddings
        ],
    }


@router.post("/exercises/similar/compare")
def compare_similar(payload: SimilarQuery) -> dict:
    if payload.exercise_id not in CATALOG.by_id:
        raise HTTPException(status_code=404, detail="Exercise not found")
    constraints = UserConstraints(
        days_per_week=3,
        max_duration_minutes=45,
        available_equipment=payload.available_equipment,
        injuries=payload.injuries,
    )
    return compare_substitutes(payload.exercise_id, constraints, limit=payload.limit)
