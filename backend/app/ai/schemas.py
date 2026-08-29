from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LLMExercisePrescription(BaseModel):
    """Fields the model is allowed to choose. Rest and duration are derived."""

    exercise_id: str
    sets: int = Field(ge=1, le=8)
    rep_min: int = Field(ge=1, le=30)
    rep_max: int = Field(ge=1, le=30)
    target_rir: int = Field(ge=0, le=5)
    target_weight_kg: float | None = None


class LLMWorkoutDay(BaseModel):
    day_index: int = Field(ge=0, le=6)
    label: str
    focus: str
    exercises: list[LLMExercisePrescription] = Field(min_length=3, max_length=8)


class LLMWorkoutPlan(BaseModel):
    days_per_week: int = Field(ge=2, le=6)
    split: str
    days: list[LLMWorkoutDay]
    reasoning: str


class GenerationMeta(BaseModel):
    source: Literal["llm", "fallback", "engine"]
    prompt_version: str | None = None
    model: str | None = None
    attempts: int = 1
    fallback_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    attempt_errors: list[str] = Field(default_factory=list)
