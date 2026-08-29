from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    days_per_week: Mapped[int] = mapped_column(Integer)
    max_duration_minutes: Mapped[int] = mapped_column(Integer)
    available_equipment: Mapped[list] = mapped_column(JSON)
    injuries: Mapped[list] = mapped_column(JSON, default=list)
    goal: Mapped[str] = mapped_column(String(32))
    training_age: Mapped[str] = mapped_column(String(32))
    excluded_exercise_ids: Mapped[list] = mapped_column(JSON, default=list)
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0)
    current_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    workouts: Mapped[list[Workout]] = relationship(back_populates="user")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    day_index: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="workouts")
    sets: Mapped[list[LoggedSet]] = relationship(back_populates="workout")


class LoggedSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workout_id: Mapped[str] = mapped_column(ForeignKey("workouts.id"))
    exercise_id: Mapped[str] = mapped_column(String(64))
    set_index: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    reps: Mapped[int] = mapped_column(Integer)
    rpe: Mapped[float | None] = mapped_column(Float, nullable=True)
    rir: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    workout: Mapped[Workout] = relationship(back_populates="sets")
