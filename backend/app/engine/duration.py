from __future__ import annotations

import math

from app.engine.catalog import Catalog
from app.engine.types import ExercisePrescription


def estimate_minutes(prescriptions: list[ExercisePrescription], catalog: Catalog) -> int:
    warmup_minutes = 4
    seconds = 0
    for index, prescription in enumerate(prescriptions):
        exercise = catalog.get(prescription.exercise_id)
        seconds += prescription.sets * (exercise.seconds_per_set + prescription.rest_seconds)
        if index < len(prescriptions) - 1:
            seconds += 20
    return math.ceil(warmup_minutes + seconds / 60)
