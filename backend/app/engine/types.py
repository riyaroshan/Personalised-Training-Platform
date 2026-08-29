from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Goal(StrEnum):
    HYPERTROPHY = "hypertrophy"
    STRENGTH = "strength"
    GENERAL = "general"


class TrainingAge(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Equipment(StrEnum):
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    CABLE = "cable"
    MACHINE = "machine"
    BODYWEIGHT = "bodyweight"
    KETTLEBELL = "kettlebell"
    BAND = "band"
    SMITH = "smith"
    EZ_BAR = "ez_bar"
    TRAP_BAR = "trap_bar"


class Muscle(StrEnum):
    CHEST = "chest"
    LATS = "lats"
    UPPER_BACK = "upper_back"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CALVES = "calves"
    CORE = "core"
    TRAPS = "traps"


class MovementPattern(StrEnum):
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE = "lunge"
    HORIZONTAL_PUSH = "horizontal_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PUSH = "vertical_push"
    VERTICAL_PULL = "vertical_pull"
    FLY = "fly"
    CURL = "curl"
    EXTENSION = "extension"
    RAISE = "raise"
    CALF = "calf"
    CORE = "core"
    CARRY = "carry"


MAJOR_MUSCLES = {
    Muscle.CHEST,
    Muscle.LATS,
    Muscle.UPPER_BACK,
    Muscle.QUADS,
    Muscle.HAMSTRINGS,
    Muscle.GLUTES,
    Muscle.SHOULDERS,
}


class Exercise(BaseModel):
    id: str
    name: str
    movement_pattern: MovementPattern
    primary_muscles: list[Muscle]
    secondary_muscles: list[Muscle] = Field(default_factory=list)
    equipment: list[Equipment]
    difficulty: int = Field(ge=1, le=5)
    is_compound: bool
    substitution_group: str
    rest_seconds: int = 90
    seconds_per_set: int = 45
    increment_kg: float = 2.5
    contraindications: list[str] = Field(default_factory=list)


class UserConstraints(BaseModel):
    days_per_week: int = Field(ge=2, le=6)
    max_duration_minutes: int = Field(ge=20, le=180)
    available_equipment: list[Equipment]
    injuries: list[str] = Field(default_factory=list)
    goal: Goal = Goal.HYPERTROPHY
    training_age: TrainingAge = TrainingAge.BEGINNER
    excluded_exercise_ids: list[str] = Field(default_factory=list)


class ExercisePrescription(BaseModel):
    exercise_id: str
    sets: int = Field(ge=1, le=8)
    rep_min: int = Field(ge=1)
    rep_max: int = Field(ge=1)
    target_rir: int = Field(ge=0, le=5)
    target_weight_kg: float | None = None
    rest_seconds: int = 90


class WorkoutPlanDay(BaseModel):
    day_index: int
    label: str
    focus: str
    estimated_minutes: int
    exercises: list[ExercisePrescription]


class WorkoutPlan(BaseModel):
    days_per_week: int
    split: str
    days: list[WorkoutPlanDay]
    reasoning: str


class WorkoutSetLog(BaseModel):
    exercise_id: str
    weight_kg: float | None
    reps: int
    rpe: float | None = None
    rir: int | None = None
    completed_at: datetime
    set_index: int
