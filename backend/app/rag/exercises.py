from __future__ import annotations

from pydantic import BaseModel

from app.engine.catalog import CATALOG, Catalog
from app.engine.substitutions import find_substitutes
from app.engine.types import Exercise, UserConstraints
from app.rag.embeddings import Embedder, cosine
from app.rag.index import get_index


class SimilarExercise(BaseModel):
    exercise_id: str
    name: str
    score: float
    equipment: list[str]
    movement_pattern: str
    substitution_group: str


def exercise_text(exercise: Exercise) -> str:
    muscles = ", ".join(item.value for item in exercise.primary_muscles + exercise.secondary_muscles)
    equipment = ", ".join(item.value for item in exercise.equipment)
    return (
        f"{exercise.name}. Movement pattern {exercise.movement_pattern.value}. "
        f"Muscles {muscles}. Equipment {equipment}. Difficulty {exercise.difficulty}. "
        f"{'Compound' if exercise.is_compound else 'Isolation'}. "
        f"Substitution group {exercise.substitution_group}."
    )


def similar_exercises(
    exercise_id: str,
    constraints: UserConstraints,
    *,
    catalog: Catalog | None = None,
    embedder: Embedder | None = None,
    limit: int = 5,
) -> list[tuple[Exercise, float]]:
    catalog = catalog or CATALOG
    source = catalog.get(exercise_id)
    embedder = embedder or get_index().embedder
    eligible = [item for item in catalog.eligible(constraints) if item.id != source.id]
    if not eligible:
        return []
    vectors = embedder.embed([exercise_text(source)] + [exercise_text(item) for item in eligible])
    source_vec, rest = vectors[0], vectors[1:]
    scored = [(exercise, round(cosine(source_vec, vector), 4)) for exercise, vector in zip(eligible, rest)]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


def compare_substitutes(
    exercise_id: str,
    constraints: UserConstraints,
    *,
    limit: int = 5,
) -> dict:
    rules = find_substitutes(exercise_id, constraints, CATALOG, limit=limit)
    embeddings = similar_exercises(exercise_id, constraints, limit=limit)
    return {
        "exercise_id": exercise_id,
        "rules": [_row(exercise, score) for exercise, score in rules],
        "embeddings": [_row(exercise, score) for exercise, score in embeddings],
    }


def _row(exercise: Exercise, score: float) -> dict:
    return SimilarExercise(
        exercise_id=exercise.id,
        name=exercise.name,
        score=score,
        equipment=[item.value for item in exercise.equipment],
        movement_pattern=exercise.movement_pattern.value,
        substitution_group=exercise.substitution_group,
    ).model_dump()
