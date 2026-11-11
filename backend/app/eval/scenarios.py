from __future__ import annotations

from pydantic import BaseModel, Field

from app.engine.types import Equipment, Goal, TrainingAge, UserConstraints

NO_BARBELL = [
    Equipment.DUMBBELL,
    Equipment.CABLE,
    Equipment.MACHINE,
    Equipment.BODYWEIGHT,
    Equipment.KETTLEBELL,
    Equipment.BAND,
]
FULL_GYM = list(Equipment)
BODYWEIGHT = [Equipment.BODYWEIGHT, Equipment.BAND]
HOME = [Equipment.DUMBBELL, Equipment.KETTLEBELL, Equipment.BAND, Equipment.BODYWEIGHT, Equipment.BARBELL]


class PlanScenario(BaseModel):
    id: str
    name: str
    constraints: UserConstraints
    expect_no_barbell: bool = False


class RagScenario(BaseModel):
    id: str
    question: str
    expected_documents: list[str]
    forbidden_documents: list[str] = Field(default_factory=list)


class CoachScenario(BaseModel):
    id: str
    question: str
    expected_tools: list[str]
    forbidden_phrases: list[str] = Field(default_factory=lambda: ["try harder", "just believe"])
    fixture: str = "bench_decline"


def plan_scenarios() -> list[PlanScenario]:
    rows: list[tuple[str, str, int, int, list[Equipment], list[str], Goal, TrainingAge, bool]] = [
        ("plan.gold_beginner_no_bb", "Beginner 3x45 no barbell hypertrophy", 3, 45, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.beginner_knee", "Beginner with knee injury", 3, 45, NO_BARBELL, ["knee"], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.beginner_shoulder", "Beginner with shoulder injury", 3, 45, NO_BARBELL, ["shoulder"], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.beginner_4x60", "Beginner 4x60", 4, 60, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.beginner_bw", "Beginner bodyweight only", 3, 45, BODYWEIGHT, [], Goal.GENERAL, TrainingAge.BEGINNER, True),
        ("plan.home_3x45", "Home gym 3x45", 3, 45, HOME, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, False),
        ("plan.inter_5x60_gym", "Intermediate 5x60 full gym", 5, 60, FULL_GYM, [], Goal.STRENGTH, TrainingAge.INTERMEDIATE, False),
        ("plan.inter_4x45_no_bb", "Intermediate 4x45 no barbell", 4, 45, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.INTERMEDIATE, True),
        ("plan.adv_6x75", "Advanced 6x75 gym", 6, 75, FULL_GYM, [], Goal.STRENGTH, TrainingAge.ADVANCED, False),
        ("plan.general_3x40", "General 3x40", 3, 40, NO_BARBELL, [], Goal.GENERAL, TrainingAge.BEGINNER, True),
        ("plan.knee_home", "Knee injury home gym", 3, 50, HOME, ["knee"], Goal.HYPERTROPHY, TrainingAge.BEGINNER, False),
        ("plan.shoulder_no_bb", "Shoulder injury no barbell", 3, 45, NO_BARBELL, ["shoulder"], Goal.STRENGTH, TrainingAge.BEGINNER, True),
        ("plan.hypertrophy_5x50", "Hypertrophy 5x50 no bb", 5, 50, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.INTERMEDIATE, True),
        ("plan.strength_3x60_gym", "Strength 3x60 gym", 3, 60, FULL_GYM, [], Goal.STRENGTH, TrainingAge.INTERMEDIATE, False),
        ("plan.beginner_6x45", "Beginner 6x45 no bb", 6, 45, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.bw_knee", "Bodyweight with knee injury", 3, 40, BODYWEIGHT, ["knee"], Goal.GENERAL, TrainingAge.BEGINNER, True),
        ("plan.full_gym_4x45", "Full gym 4x45 hypertrophy", 4, 45, FULL_GYM, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, False),
        ("plan.lower_back", "Lower-back caution no bb", 3, 45, NO_BARBELL, ["lower_back"], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.inter_3x45_gym", "Intermediate 3x45 gym", 3, 45, FULL_GYM, [], Goal.HYPERTROPHY, TrainingAge.INTERMEDIATE, False),
        ("plan.beginner_home_4x55", "Beginner home 4x55", 4, 55, HOME, [], Goal.GENERAL, TrainingAge.BEGINNER, False),
        ("plan.adv_4x60_no_bb", "Advanced 4x60 no barbell", 4, 60, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.ADVANCED, True),
        ("plan.strength_4x50_no_bb", "Strength 4x50 no barbell", 4, 50, NO_BARBELL, [], Goal.STRENGTH, TrainingAge.BEGINNER, True),
        ("plan.hypertrophy_3x30", "Short 30-min hypertrophy", 3, 30, NO_BARBELL, [], Goal.HYPERTROPHY, TrainingAge.BEGINNER, True),
        ("plan.gym_knee_shoulder", "Gym with knee+shoulder", 3, 60, FULL_GYM, ["knee", "shoulder"], Goal.GENERAL, TrainingAge.BEGINNER, False),
    ]
    scenarios = []
    for sid, name, days, minutes, gear, injuries, goal, age, no_bb in rows:
        scenarios.append(
            PlanScenario(
                id=sid,
                name=name,
                expect_no_barbell=no_bb,
                constraints=UserConstraints(
                    days_per_week=days,
                    max_duration_minutes=minutes,
                    available_equipment=gear,
                    injuries=injuries,
                    goal=goal,
                    training_age=age,
                ),
            )
        )
    return scenarios


def rag_scenarios() -> list[RagScenario]:
    return [
        RagScenario(
            id="rag.chest_frequency",
            question="Should I train chest twice or three times a week?",
            expected_documents=["hypertrophy_frequency"],
            forbidden_documents=["injury_shoulder", "injury_knee"],
        ),
        RagScenario(
            id="rag.weekly_volume",
            question="How many hard sets per muscle per week for hypertrophy?",
            expected_documents=["weekly_volume"],
        ),
        RagScenario(
            id="rag.overload",
            question="How does this app progress load with double progression?",
            expected_documents=["progressive_overload", "platform_methodology"],
        ),
        RagScenario(
            id="rag.deload",
            question="When should I deload?",
            expected_documents=["deloads"],
        ),
        RagScenario(
            id="rag.rir",
            question="What RIR should hypertrophy sets use?",
            expected_documents=["rir_rpe"],
        ),
        RagScenario(
            id="rag.shoulder",
            question="I have a cranky shoulder. What pressing should I avoid?",
            expected_documents=["injury_shoulder"],
            forbidden_documents=["hypertrophy_frequency"],
        ),
        RagScenario(
            id="rag.knee",
            question="How should I squat with cranky knees?",
            expected_documents=["injury_knee"],
        ),
        RagScenario(
            id="rag.fly",
            question="What is a fly movement and how is it different from a press?",
            expected_documents=["exercise_fly_family", "movement_patterns"],
        ),
        RagScenario(
            id="rag.beginner",
            question="How should a beginner program the first weeks?",
            expected_documents=["beginner_programming"],
        ),
        RagScenario(
            id="rag.press",
            question="How do I choose a chest press variation?",
            expected_documents=["exercise_press_family"],
        ),
    ]


def coach_scenarios() -> list[CoachScenario]:
    return [
        CoachScenario(
            id="coach.bench_plateau",
            question="Why hasn't my bench improved?",
            expected_tools=["get_exercise_history", "get_muscle_volume", "get_recovery_scores"],
        ),
        CoachScenario(
            id="coach.substitute_fly",
            question="The cable machine is occupied. Give me a substitute for cable fly.",
            expected_tools=["find_exercise_substitutes"],
            fixture="empty",
        ),
        CoachScenario(
            id="coach.recovery",
            question="How is my recovery looking?",
            expected_tools=["get_recovery_scores"],
        ),
        CoachScenario(
            id="coach.progress",
            question="Is my bench stalling or improving?",
            expected_tools=["get_exercise_history"],
        ),
        CoachScenario(
            id="coach.volume",
            question="Am I doing enough chest volume?",
            expected_tools=["get_muscle_volume"],
        ),
        CoachScenario(
            id="coach.recent",
            question="What have I trained recently?",
            expected_tools=["get_recent_workouts"],
            fixture="empty",
        ),
    ]
