from __future__ import annotations

from app.engine.types import Equipment, Exercise, MovementPattern, Muscle, UserConstraints


def _e(
    id: str,
    name: str,
    pattern: MovementPattern,
    primary: list[Muscle],
    equipment: list[Equipment],
    *,
    secondary: list[Muscle] | None = None,
    difficulty: int = 2,
    compound: bool = True,
    group: str,
    rest: int = 90,
    work: int = 45,
    inc: float = 2.5,
    contra: tuple[str, ...] = (),
) -> Exercise:
    return Exercise(
        id=id,
        name=name,
        movement_pattern=pattern,
        primary_muscles=primary,
        secondary_muscles=secondary or [],
        equipment=equipment,
        difficulty=difficulty,
        is_compound=compound,
        substitution_group=group,
        rest_seconds=rest,
        seconds_per_set=work,
        increment_kg=inc,
        contraindications=list(contra),
    )


EXERCISES: list[Exercise] = [
    # Squat pattern
    _e("barbell_back_squat", "Barbell Back Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.BARBELL], secondary=[Muscle.GLUTES, Muscle.CORE], difficulty=4, group="squat", inc=5, contra=("knee", "lower_back")),
    _e("front_squat", "Front Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.BARBELL], secondary=[Muscle.CORE, Muscle.GLUTES], difficulty=5, group="squat", inc=5, contra=("knee", "wrist")),
    _e("goblet_squat", "Goblet Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.DUMBBELL], secondary=[Muscle.GLUTES, Muscle.CORE], difficulty=2, group="squat", contra=("knee",)),
    _e("leg_press", "Leg Press", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.MACHINE], secondary=[Muscle.GLUTES], difficulty=2, group="squat", rest=90, contra=("knee",)),
    _e("hack_squat", "Hack Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.MACHINE], secondary=[Muscle.GLUTES], difficulty=3, group="squat", contra=("knee",)),
    _e("smith_squat", "Smith Machine Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.SMITH], secondary=[Muscle.GLUTES], difficulty=3, group="squat", contra=("knee",)),
    _e("bodyweight_squat", "Bodyweight Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.BODYWEIGHT], secondary=[Muscle.GLUTES], difficulty=1, group="squat", rest=60, contra=("knee",)),
    _e("belt_squat", "Belt Squat", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.MACHINE], secondary=[Muscle.GLUTES], difficulty=3, group="squat", contra=("knee",)),
    # Lunge / split
    _e("bulgarian_split_squat", "Bulgarian Split Squat", MovementPattern.LUNGE, [Muscle.QUADS], [Equipment.DUMBBELL], secondary=[Muscle.GLUTES], difficulty=3, group="split_squat", contra=("knee",)),
    _e("walking_lunge", "Walking Lunge", MovementPattern.LUNGE, [Muscle.QUADS], [Equipment.DUMBBELL], secondary=[Muscle.GLUTES], difficulty=3, group="split_squat", contra=("knee",)),
    _e("reverse_lunge", "Reverse Lunge", MovementPattern.LUNGE, [Muscle.QUADS], [Equipment.DUMBBELL], secondary=[Muscle.GLUTES], difficulty=2, group="split_squat", contra=("knee",)),
    _e("bodyweight_lunge", "Bodyweight Lunge", MovementPattern.LUNGE, [Muscle.QUADS], [Equipment.BODYWEIGHT], secondary=[Muscle.GLUTES], difficulty=1, group="split_squat", rest=60, contra=("knee",)),
    # Hinge
    _e("barbell_rdl", "Barbell Romanian Deadlift", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.BARBELL], secondary=[Muscle.GLUTES, Muscle.UPPER_BACK], difficulty=4, group="hinge", inc=5, contra=("lower_back",)),
    _e("conventional_deadlift", "Conventional Deadlift", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.BARBELL], secondary=[Muscle.HAMSTRINGS, Muscle.UPPER_BACK, Muscle.CORE], difficulty=5, group="hinge", inc=5, contra=("lower_back",)),
    _e("trap_bar_deadlift", "Trap Bar Deadlift", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.TRAP_BAR], secondary=[Muscle.QUADS, Muscle.HAMSTRINGS], difficulty=3, group="hinge", inc=5, contra=("lower_back",)),
    _e("db_rdl", "Dumbbell Romanian Deadlift", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.DUMBBELL], secondary=[Muscle.GLUTES], difficulty=2, group="hinge", contra=("lower_back",)),
    _e("kb_rdl", "Kettlebell Romanian Deadlift", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.KETTLEBELL], secondary=[Muscle.GLUTES], difficulty=2, group="hinge", contra=("lower_back",)),
    _e("cable_pull_through", "Cable Pull-Through", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.CABLE], secondary=[Muscle.HAMSTRINGS], difficulty=2, group="hinge"),
    _e("back_extension", "Back Extension", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.MACHINE], secondary=[Muscle.GLUTES, Muscle.CORE], difficulty=2, group="hinge", rest=75),
    _e("kb_swing", "Kettlebell Swing", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.KETTLEBELL], secondary=[Muscle.HAMSTRINGS, Muscle.CORE], difficulty=3, group="hinge"),
    _e("hip_thrust", "Barbell Hip Thrust", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.BARBELL], secondary=[Muscle.HAMSTRINGS], difficulty=3, group="hip_thrust"),
    _e("glute_bridge", "Glute Bridge", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.BODYWEIGHT], secondary=[Muscle.HAMSTRINGS], difficulty=1, group="hip_thrust", rest=60),
    _e("db_hip_thrust", "Dumbbell Hip Thrust", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.DUMBBELL], secondary=[Muscle.HAMSTRINGS], difficulty=2, group="hip_thrust"),
    _e("machine_hip_thrust", "Machine Hip Thrust", MovementPattern.HINGE, [Muscle.GLUTES], [Equipment.MACHINE], secondary=[Muscle.HAMSTRINGS], difficulty=2, group="hip_thrust"),
    # Horizontal push
    _e("barbell_bench_press", "Barbell Bench Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.BARBELL], secondary=[Muscle.TRICEPS, Muscle.SHOULDERS], difficulty=3, group="horizontal_press", contra=("shoulder",)),
    _e("db_bench_press", "Dumbbell Bench Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.DUMBBELL], secondary=[Muscle.TRICEPS, Muscle.SHOULDERS], difficulty=2, group="horizontal_press", contra=("shoulder",)),
    _e("incline_barbell_press", "Incline Barbell Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.BARBELL], secondary=[Muscle.SHOULDERS, Muscle.TRICEPS], difficulty=4, group="incline_press", contra=("shoulder",)),
    _e("incline_db_press", "Incline Dumbbell Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.DUMBBELL], secondary=[Muscle.SHOULDERS, Muscle.TRICEPS], difficulty=2, group="incline_press", contra=("shoulder",)),
    _e("machine_chest_press", "Machine Chest Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.MACHINE], secondary=[Muscle.TRICEPS, Muscle.SHOULDERS], difficulty=1, group="horizontal_press", contra=("shoulder",)),
    _e("push_up", "Push-Up", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.BODYWEIGHT], secondary=[Muscle.TRICEPS, Muscle.SHOULDERS, Muscle.CORE], difficulty=2, group="horizontal_press", rest=75, contra=("shoulder", "wrist")),
    _e("smith_bench_press", "Smith Machine Bench Press", MovementPattern.HORIZONTAL_PUSH, [Muscle.CHEST], [Equipment.SMITH], secondary=[Muscle.TRICEPS, Muscle.SHOULDERS], difficulty=2, group="horizontal_press", contra=("shoulder",)),
    # Fly
    _e("cable_fly", "Cable Fly", MovementPattern.FLY, [Muscle.CHEST], [Equipment.CABLE], difficulty=2, compound=False, group="fly", rest=60, contra=("shoulder",)),
    _e("pec_deck", "Pec Deck", MovementPattern.FLY, [Muscle.CHEST], [Equipment.MACHINE], difficulty=1, compound=False, group="fly", rest=60, contra=("shoulder",)),
    _e("db_fly", "Dumbbell Fly", MovementPattern.FLY, [Muscle.CHEST], [Equipment.DUMBBELL], difficulty=2, compound=False, group="fly", rest=60, contra=("shoulder",)),
    _e("band_chest_fly", "Band Chest Fly", MovementPattern.FLY, [Muscle.CHEST], [Equipment.BAND], difficulty=1, compound=False, group="fly", rest=45),
    # Vertical push
    _e("barbell_ohp", "Barbell Overhead Press", MovementPattern.VERTICAL_PUSH, [Muscle.SHOULDERS], [Equipment.BARBELL], secondary=[Muscle.TRICEPS, Muscle.CORE], difficulty=4, group="vertical_press", contra=("shoulder", "lower_back")),
    _e("db_shoulder_press", "Dumbbell Shoulder Press", MovementPattern.VERTICAL_PUSH, [Muscle.SHOULDERS], [Equipment.DUMBBELL], secondary=[Muscle.TRICEPS], difficulty=2, group="vertical_press", contra=("shoulder",)),
    _e("machine_shoulder_press", "Machine Shoulder Press", MovementPattern.VERTICAL_PUSH, [Muscle.SHOULDERS], [Equipment.MACHINE], secondary=[Muscle.TRICEPS], difficulty=1, group="vertical_press", contra=("shoulder",)),
    _e("pike_push_up", "Pike Push-Up", MovementPattern.VERTICAL_PUSH, [Muscle.SHOULDERS], [Equipment.BODYWEIGHT], secondary=[Muscle.TRICEPS], difficulty=3, group="vertical_press", rest=75, contra=("shoulder", "wrist")),
    # Horizontal pull
    _e("barbell_row", "Barbell Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.BARBELL], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=3, group="row", contra=("lower_back",)),
    _e("db_row", "Dumbbell Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.DUMBBELL], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=2, group="row"),
    _e("seated_cable_row", "Seated Cable Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.CABLE], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=2, group="row"),
    _e("chest_supported_row", "Chest-Supported Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.DUMBBELL], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=2, group="row"),
    _e("machine_row", "Machine Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.MACHINE], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=1, group="row"),
    _e("inverted_row", "Inverted Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.BODYWEIGHT], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=2, group="row", rest=75),
    _e("band_row", "Band Row", MovementPattern.HORIZONTAL_PULL, [Muscle.UPPER_BACK], [Equipment.BAND], secondary=[Muscle.LATS, Muscle.BICEPS], difficulty=1, group="row", rest=60),
    # Vertical pull
    _e("pull_up", "Pull-Up", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.BODYWEIGHT], secondary=[Muscle.UPPER_BACK, Muscle.BICEPS], difficulty=4, group="pulldown", contra=("shoulder",)),
    _e("chin_up", "Chin-Up", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.BODYWEIGHT], secondary=[Muscle.BICEPS, Muscle.UPPER_BACK], difficulty=4, group="pulldown", contra=("shoulder",)),
    _e("lat_pulldown", "Lat Pulldown", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.CABLE], secondary=[Muscle.UPPER_BACK, Muscle.BICEPS], difficulty=2, group="pulldown"),
    _e("machine_pulldown", "Machine Pulldown", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.MACHINE], secondary=[Muscle.BICEPS], difficulty=1, group="pulldown"),
    _e("band_pulldown", "Band Pulldown", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.BAND], secondary=[Muscle.BICEPS], difficulty=1, group="pulldown", rest=60),
    _e("assisted_pull_up", "Assisted Pull-Up", MovementPattern.VERTICAL_PULL, [Muscle.LATS], [Equipment.MACHINE], secondary=[Muscle.UPPER_BACK, Muscle.BICEPS], difficulty=2, group="pulldown"),
    # Arms
    _e("db_curl", "Dumbbell Curl", MovementPattern.CURL, [Muscle.BICEPS], [Equipment.DUMBBELL], difficulty=1, compound=False, group="curl", rest=60),
    _e("hammer_curl", "Hammer Curl", MovementPattern.CURL, [Muscle.BICEPS], [Equipment.DUMBBELL], difficulty=1, compound=False, group="curl", rest=60),
    _e("cable_curl", "Cable Curl", MovementPattern.CURL, [Muscle.BICEPS], [Equipment.CABLE], difficulty=1, compound=False, group="curl", rest=60),
    _e("barbell_curl", "Barbell Curl", MovementPattern.CURL, [Muscle.BICEPS], [Equipment.BARBELL], difficulty=2, compound=False, group="curl", rest=60),
    _e("band_curl", "Band Curl", MovementPattern.CURL, [Muscle.BICEPS], [Equipment.BAND], difficulty=1, compound=False, group="curl", rest=45),
    _e("cable_pushdown", "Cable Triceps Pushdown", MovementPattern.EXTENSION, [Muscle.TRICEPS], [Equipment.CABLE], difficulty=1, compound=False, group="triceps", rest=60),
    _e("overhead_db_extension", "Overhead Dumbbell Extension", MovementPattern.EXTENSION, [Muscle.TRICEPS], [Equipment.DUMBBELL], difficulty=2, compound=False, group="triceps", rest=60, contra=("shoulder",)),
    _e("skullcrusher", "Skullcrusher", MovementPattern.EXTENSION, [Muscle.TRICEPS], [Equipment.EZ_BAR], difficulty=3, compound=False, group="triceps", rest=75, contra=("elbow",)),
    _e("bench_dip", "Bench Dip", MovementPattern.EXTENSION, [Muscle.TRICEPS], [Equipment.BODYWEIGHT], difficulty=2, compound=False, group="triceps", rest=60, contra=("shoulder",)),
    _e("machine_triceps", "Machine Triceps Extension", MovementPattern.EXTENSION, [Muscle.TRICEPS], [Equipment.MACHINE], difficulty=1, compound=False, group="triceps", rest=60),
    # Delts / upper back accessories
    _e("db_lateral_raise", "Dumbbell Lateral Raise", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.DUMBBELL], difficulty=1, compound=False, group="lateral", rest=45),
    _e("cable_lateral_raise", "Cable Lateral Raise", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.CABLE], difficulty=2, compound=False, group="lateral", rest=45),
    _e("machine_lateral_raise", "Machine Lateral Raise", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.MACHINE], difficulty=1, compound=False, group="lateral", rest=45),
    _e("face_pull", "Face Pull", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.CABLE], secondary=[Muscle.UPPER_BACK], difficulty=1, compound=False, group="rear_delt", rest=45),
    _e("rear_delt_fly", "Rear Delt Fly", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.DUMBBELL], secondary=[Muscle.UPPER_BACK], difficulty=1, compound=False, group="rear_delt", rest=45),
    _e("band_pull_apart", "Band Pull-Apart", MovementPattern.RAISE, [Muscle.SHOULDERS], [Equipment.BAND], secondary=[Muscle.UPPER_BACK], difficulty=1, compound=False, group="rear_delt", rest=30),
    # Calves / core / carry
    _e("standing_calf_raise", "Standing Calf Raise", MovementPattern.CALF, [Muscle.CALVES], [Equipment.MACHINE], difficulty=1, compound=False, group="calf", rest=45),
    _e("seated_calf_raise", "Seated Calf Raise", MovementPattern.CALF, [Muscle.CALVES], [Equipment.MACHINE], difficulty=1, compound=False, group="calf", rest=45),
    _e("db_calf_raise", "Dumbbell Calf Raise", MovementPattern.CALF, [Muscle.CALVES], [Equipment.DUMBBELL], difficulty=1, compound=False, group="calf", rest=45),
    _e("plank", "Plank", MovementPattern.CORE, [Muscle.CORE], [Equipment.BODYWEIGHT], difficulty=1, compound=False, group="core", rest=45, work=40),
    _e("cable_crunch", "Cable Crunch", MovementPattern.CORE, [Muscle.CORE], [Equipment.CABLE], difficulty=1, compound=False, group="core", rest=45),
    _e("hanging_knee_raise", "Hanging Knee Raise", MovementPattern.CORE, [Muscle.CORE], [Equipment.BODYWEIGHT], difficulty=3, compound=False, group="core", rest=60, contra=("shoulder",)),
    _e("dead_bug", "Dead Bug", MovementPattern.CORE, [Muscle.CORE], [Equipment.BODYWEIGHT], difficulty=1, compound=False, group="core", rest=30, work=40),
    _e("farmers_carry", "Farmer's Carry", MovementPattern.CARRY, [Muscle.CORE], [Equipment.DUMBBELL], secondary=[Muscle.TRAPS], difficulty=2, group="carry", rest=60),
    _e("leg_curl", "Lying Leg Curl", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.MACHINE], difficulty=1, compound=False, group="leg_curl", rest=60),
    _e("seated_leg_curl", "Seated Leg Curl", MovementPattern.HINGE, [Muscle.HAMSTRINGS], [Equipment.MACHINE], difficulty=1, compound=False, group="leg_curl", rest=60),
    _e("leg_extension", "Leg Extension", MovementPattern.SQUAT, [Muscle.QUADS], [Equipment.MACHINE], difficulty=1, compound=False, group="leg_extension", rest=60, contra=("knee",)),
]


class Catalog:
    def __init__(self, exercises: list[Exercise]):
        self.exercises = exercises
        self.by_id = {exercise.id: exercise for exercise in exercises}

    def get(self, exercise_id: str) -> Exercise:
        try:
            return self.by_id[exercise_id]
        except KeyError as exc:
            raise KeyError(f"Unknown exercise: {exercise_id}") from exc

    def eligible(self, constraints: UserConstraints) -> list[Exercise]:
        allowed = set(constraints.available_equipment)
        injuries = set(constraints.injuries)
        excluded = set(constraints.excluded_exercise_ids)
        result: list[Exercise] = []
        for exercise in self.exercises:
            if exercise.id in excluded:
                continue
            if not set(exercise.equipment).issubset(allowed):
                continue
            if injuries.intersection(exercise.contraindications):
                continue
            result.append(exercise)
        return result


CATALOG = Catalog(EXERCISES)
