from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    topic: str
    audience: str = "all"
    text: str


DOCUMENTS: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="hypertrophy_frequency",
        title="Muscle frequency for hypertrophy",
        topic="hypertrophy",
        text=(
            "Should you train chest twice or three times a week? "
            "Training a muscle twice per week is a reliable default for hypertrophy. "
            "Spreading 10 to 20 weekly hard sets across two sessions usually beats cramming "
            "the same volume into one exhausting day. Three times per week can work if each "
            "session is shorter — for example 4 to 8 chest sets, not 12 — so recovery stays intact. "
            "Beginners often grow well on two chest days because they recover easily and keep "
            "technique high. Choose three weekly chest sessions only if sleep, joints, and "
            "performance between sessions stay stable. Frequency is a way to organize volume, "
            "not a magic number."
        ),
    ),
    KnowledgeDocument(
        id="weekly_volume",
        title="Weekly set volume landmarks",
        topic="hypertrophy",
        text=(
            "Most lifters add muscle in a range of roughly 8 to 20 hard sets per muscle per week. "
            "Beginners often progress at the low end. Intermediate lifters usually live in the middle. "
            "Junk volume is extra sets that do not improve the stimulus but add fatigue. "
            "If performance drops for two sessions, reduce volume before adding another training day. "
            "This platform's engine targets moderate volume first, then progresses load."
        ),
    ),
    KnowledgeDocument(
        id="progressive_overload",
        title="Progressive overload and double progression",
        topic="methodology",
        text=(
            "Progressive overload means adding stress over time: more load, more reps in a range, "
            "or cleaner reps at the same load. This app uses double progression. Stay in the assigned "
            "rep range. When every set hits the top of the range, increase weight by the exercise increment. "
            "If you miss the floor of the range, keep the load or deload. Do not jump load just because "
            "the calendar moved. Log RIR so the next prescription is honest."
        ),
    ),
    KnowledgeDocument(
        id="deloads",
        title="Deloads and fatigue",
        topic="recovery",
        text=(
            "A deload is a planned reduction in load and sets so you can recover. "
            "This engine reduces volume and load about every fifth week of completed sessions. "
            "You also deload if performance keeps missing rep minimums. "
            "A deload is not a failure. It is how you keep progressive overload sustainable."
        ),
    ),
    KnowledgeDocument(
        id="rir_rpe",
        title="RIR and RPE targets",
        topic="methodology",
        text=(
            "RIR means reps in reserve. RPE is rating of perceived exertion. "
            "Hypertrophy work usually targets about 2 RIR so you can accumulate volume without "
            "failing sets. Strength work often sits closer to 1 RIR on main compounds. "
            "If every set is to failure, quality and next-session performance usually drop. "
            "Log RIR on each set; the progression engine reads it."
        ),
    ),
    KnowledgeDocument(
        id="injury_shoulder",
        title="Shoulder and rotator cuff precautions",
        topic="injury",
        text=(
            "Acute shoulder or rotator cuff pain is outside what an AI coach should push through. "
            "Avoid prescribing heavy overhead pressing, dips, or aggressive flyes through sharp pain. "
            "This catalog marks many vertical presses and flyes as contraindicated for shoulder issues. "
            "A torn rotator cuff yesterday is a medical problem, not a programming puzzle. "
            "Stop loading the painful range and use a clinician. The coach may suggest machine or "
            "supported work only when the constraint is a mild historical niggle, not an acute tear."
        ),
    ),
    KnowledgeDocument(
        id="injury_knee",
        title="Knee-friendly lower body choices",
        topic="injury",
        text=(
            "Knee pain often rules out deep squats, lunges, and loaded knee extension. "
            "Hinge patterns such as hip thrusts, pull-throughs, and supported back extensions "
            "can keep the posterior chain working with less knee stress. "
            "Do not grind through sharp knee pain to hit a squat slot. Substitute instead."
        ),
    ),
    KnowledgeDocument(
        id="movement_patterns",
        title="Movement patterns used by the engine",
        topic="methodology",
        text=(
            "The programming engine fills slots by movement pattern: squat, hinge, lunge, "
            "horizontal push, horizontal pull, vertical push, vertical pull, fly, curl, extension, "
            "raise, calf, core, and carry. That is why a session can replace barbell bench with "
            "dumbbell bench or a machine press — same horizontal push pattern, different equipment. "
            "Cover the week with a squat or lunge, a hinge, a push, and a pull."
        ),
    ),
    KnowledgeDocument(
        id="exercise_fly_family",
        title="Chest fly variations",
        topic="exercise",
        text=(
            "Cable fly, pec deck, dumbbell fly, and cable crossover all train the chest through "
            "horizontal adduction with less triceps than a press. They are isolation patterns, "
            "not the main strength builder. If the cable machine is occupied, pec deck and dumbbell "
            "fly are the closest substitutes. Filter by available equipment: dumbbells point to "
            "dumbbell fly, not pec deck. Keep a slight elbow bend and do not turn a fly into a press."
        ),
    ),
    KnowledgeDocument(
        id="exercise_press_family",
        title="Horizontal press variations",
        topic="exercise",
        text=(
            "Barbell bench, dumbbell bench, machine chest press, and push-ups are horizontal presses. "
            "They load chest, triceps, and anterior delts. Dumbbells allow a longer range and easier "
            "shoulder-friendly path. Machines reduce stability demand, which is useful for beginners "
            "or when recovering. Push-ups need no equipment. Do not treat a fly as a press substitute "
            "when you still need compound pressing volume."
        ),
    ),
    KnowledgeDocument(
        id="beginner_programming",
        title="Beginner full-body programming",
        topic="methodology",
        audience="beginner",
        text=(
            "Beginners with three days per week usually do best on full-body sessions, not a body-part "
            "split. Each session includes a squat or lunge, a hinge, a push, and a pull, then optional "
            "isolation if time remains. Forty-five minutes is enough if rest is controlled. "
            "This is the split the deterministic engine chooses for a beginner hypertrophy athlete."
        ),
    ),
    KnowledgeDocument(
        id="platform_methodology",
        title="How this training platform decides workouts",
        topic="methodology",
        text=(
            "This product is a deterministic training engine first. User goals and constraints select "
            "a split. An exercise catalog with equipment, muscles, and contraindications fills slots. "
            "Duration is estimated from sets and rest, then trimmed to the time cap. "
            "Progression reads logged sets. An LLM may propose a plan only as structured output that "
            "must pass the same validators. If the model fails, the engine is the fallback. "
            "User lifting history is operational data for tools, not RAG. RAG is for training principles."
        ),
    ),
]
