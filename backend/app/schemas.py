from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.engine.types import (
    Equipment,
    ExercisePrescription,
    Goal,
    TrainingAge,
    WorkoutPlan,
)
from app.ai.schemas import GenerationMeta


class UserCreate(BaseModel):
    name: str
    days_per_week: int = Field(ge=2, le=6)
    max_duration_minutes: int = Field(ge=20, le=180)
    available_equipment: list[Equipment]
    injuries: list[str] = Field(default_factory=list)
    goal: Goal = Goal.HYPERTROPHY
    training_age: TrainingAge = TrainingAge.BEGINNER
    excluded_exercise_ids: list[str] = Field(default_factory=list)


class UserPublic(BaseModel):
    id: str
    name: str
    days_per_week: int
    max_duration_minutes: int
    available_equipment: list[str]
    injuries: list[str]
    goal: str
    training_age: str
    sessions_completed: int
    current_plan: WorkoutPlan | None = None


class PlanResponse(BaseModel):
    user_id: str
    plan: WorkoutPlan
    violations: list[str] = Field(default_factory=list)
    generation: GenerationMeta | None = None


class WorkoutStart(BaseModel):
    day_index: int = Field(ge=0)


class SetLogCreate(BaseModel):
    exercise_id: str
    set_index: int = Field(ge=0)
    weight_kg: float | None = None
    reps: int = Field(ge=0)
    rpe: float | None = Field(default=None, ge=1, le=10)
    rir: int | None = Field(default=None, ge=0, le=5)


class LoggedSetPublic(BaseModel):
    id: str
    exercise_id: str
    set_index: int
    weight_kg: float | None
    reps: int
    rpe: float | None
    rir: int | None
    completed_at: datetime


class WorkoutPublic(BaseModel):
    id: str
    user_id: str
    day_index: int
    label: str
    started_at: datetime
    completed_at: datetime | None
    sets: list[LoggedSetPublic] = Field(default_factory=list)


class ExercisePublic(BaseModel):
    id: str
    name: str
    movement_pattern: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    equipment: list[str]
    difficulty: int
    is_compound: bool
    substitution_group: str


class SubstitutePublic(BaseModel):
    exercise: ExercisePublic
    score: float


class DayPreview(BaseModel):
    day: int
    label: str
    estimated_minutes: int
    exercises: list[ExercisePrescription]
