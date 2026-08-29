from __future__ import annotations

from dataclasses import dataclass

from app.engine.types import MovementPattern, Muscle, TrainingAge


@dataclass(frozen=True)
class Slot:
    pattern: MovementPattern
    require_compound: bool = False
    primary: Muscle | None = None
    optional: bool = False


@dataclass(frozen=True)
class DayTemplate:
    label: str
    focus: str
    slots: tuple[Slot, ...]


def select_split(days_per_week: int, training_age: TrainingAge) -> tuple[str, tuple[DayTemplate, ...]]:
    if days_per_week == 2:
        return "full_body_ab", FULL_BODY_2
    if days_per_week == 3:
        return "full_body_abc", FULL_BODY_3
    if days_per_week == 4:
        return "upper_lower", UPPER_LOWER_4
    if days_per_week == 5:
        if training_age == TrainingAge.BEGINNER:
            return "upper_lower_full", UPPER_LOWER_FULL_5
        return "ppl_ul", PPL_UL_5
    return "ppl_ppl", PPL_6


FULL_BODY_2 = (
    DayTemplate(
        "Full Body A",
        "squat_push_pull",
        (
            Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
            Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.HAMSTRINGS),
            Slot(MovementPattern.CORE, optional=True),
        ),
    ),
    DayTemplate(
        "Full Body B",
        "hinge_vertical",
        (
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.GLUTES),
            Slot(MovementPattern.VERTICAL_PUSH, require_compound=True, primary=Muscle.SHOULDERS),
            Slot(MovementPattern.VERTICAL_PULL, require_compound=True, primary=Muscle.LATS),
            Slot(MovementPattern.LUNGE, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.FLY, optional=True, primary=Muscle.CHEST),
        ),
    ),
)

FULL_BODY_3 = (
    DayTemplate(
        "Full Body A",
        "squat_emphasis",
        (
            Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
            Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.HAMSTRINGS),
            Slot(MovementPattern.CORE, optional=True),
        ),
    ),
    DayTemplate(
        "Full Body B",
        "vertical_emphasis",
        (
            Slot(MovementPattern.LUNGE, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.VERTICAL_PUSH, require_compound=True, primary=Muscle.SHOULDERS),
            Slot(MovementPattern.VERTICAL_PULL, require_compound=True, primary=Muscle.LATS),
            Slot(MovementPattern.FLY, optional=True, primary=Muscle.CHEST),
            Slot(MovementPattern.CURL, optional=True, primary=Muscle.BICEPS),
        ),
    ),
    DayTemplate(
        "Full Body C",
        "hinge_emphasis",
        (
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.GLUTES),
            Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
            Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
            Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.EXTENSION, optional=True, primary=Muscle.TRICEPS),
        ),
    ),
)

_UPPER = (
    Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
    Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
    Slot(MovementPattern.VERTICAL_PUSH, require_compound=True, primary=Muscle.SHOULDERS),
    Slot(MovementPattern.VERTICAL_PULL, require_compound=True, primary=Muscle.LATS),
    Slot(MovementPattern.FLY, optional=True, primary=Muscle.CHEST),
    Slot(MovementPattern.CURL, optional=True, primary=Muscle.BICEPS),
)

_LOWER = (
    Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
    Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.HAMSTRINGS),
    Slot(MovementPattern.LUNGE, require_compound=True, primary=Muscle.QUADS),
    Slot(MovementPattern.CALF, optional=True),
    Slot(MovementPattern.CORE, optional=True),
)

UPPER_LOWER_4 = (
    DayTemplate("Upper A", "push_pull", _UPPER),
    DayTemplate("Lower A", "squat_hinge", _LOWER),
    DayTemplate(
        "Upper B",
        "vertical_bias",
        (
            Slot(MovementPattern.VERTICAL_PUSH, require_compound=True, primary=Muscle.SHOULDERS),
            Slot(MovementPattern.VERTICAL_PULL, require_compound=True, primary=Muscle.LATS),
            Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
            Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
            Slot(MovementPattern.RAISE, optional=True, primary=Muscle.SHOULDERS),
            Slot(MovementPattern.EXTENSION, optional=True, primary=Muscle.TRICEPS),
        ),
    ),
    DayTemplate(
        "Lower B",
        "hinge_bias",
        (
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.GLUTES),
            Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.LUNGE, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.CALF, optional=True),
            Slot(MovementPattern.CORE, optional=True),
        ),
    ),
)

UPPER_LOWER_FULL_5 = UPPER_LOWER_4 + (
    DayTemplate(
        "Full Body",
        "coverage",
        (
            Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
            Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
            Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
            Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.HAMSTRINGS),
            Slot(MovementPattern.CORE, optional=True),
        ),
    ),
)

_PUSH = (
    Slot(MovementPattern.HORIZONTAL_PUSH, require_compound=True, primary=Muscle.CHEST),
    Slot(MovementPattern.VERTICAL_PUSH, require_compound=True, primary=Muscle.SHOULDERS),
    Slot(MovementPattern.FLY, optional=True, primary=Muscle.CHEST),
    Slot(MovementPattern.EXTENSION, optional=True, primary=Muscle.TRICEPS),
    Slot(MovementPattern.RAISE, optional=True, primary=Muscle.SHOULDERS),
)

_PULL = (
    Slot(MovementPattern.VERTICAL_PULL, require_compound=True, primary=Muscle.LATS),
    Slot(MovementPattern.HORIZONTAL_PULL, require_compound=True, primary=Muscle.UPPER_BACK),
    Slot(MovementPattern.CURL, optional=True, primary=Muscle.BICEPS),
    Slot(MovementPattern.RAISE, optional=True, primary=Muscle.SHOULDERS),
)

_LEGS = (
    Slot(MovementPattern.SQUAT, require_compound=True, primary=Muscle.QUADS),
    Slot(MovementPattern.HINGE, require_compound=True, primary=Muscle.HAMSTRINGS),
    Slot(MovementPattern.LUNGE, require_compound=True, primary=Muscle.QUADS),
    Slot(MovementPattern.CALF, optional=True),
    Slot(MovementPattern.CORE, optional=True),
)

PPL_UL_5 = (
    DayTemplate("Push", "pressing", _PUSH),
    DayTemplate("Pull", "rowing_and_pulldowns", _PULL),
    DayTemplate("Legs", "squat_hinge", _LEGS),
    DayTemplate("Upper", "push_pull", _UPPER),
    DayTemplate("Lower", "squat_hinge", _LOWER),
)

PPL_6 = (
    DayTemplate("Push A", "pressing", _PUSH),
    DayTemplate("Pull A", "rowing_and_pulldowns", _PULL),
    DayTemplate("Legs A", "squat_hinge", _LEGS),
    DayTemplate("Push B", "pressing", _PUSH),
    DayTemplate("Pull B", "rowing_and_pulldowns", _PULL),
    DayTemplate("Legs B", "hinge_bias", _LEGS),
)
