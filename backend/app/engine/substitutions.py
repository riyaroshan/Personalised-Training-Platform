from __future__ import annotations

from app.engine.catalog import Catalog
from app.engine.types import Exercise, UserConstraints


def find_substitutes(
    exercise_id: str,
    constraints: UserConstraints,
    catalog: Catalog,
    *,
    limit: int = 5,
) -> list[tuple[Exercise, float]]:
    source = catalog.get(exercise_id)
    scored: list[tuple[Exercise, float]] = []
    for candidate in catalog.eligible(constraints):
        if candidate.id == source.id:
            continue
        score = _similarity(source, candidate)
        if score <= 0:
            continue
        scored.append((candidate, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


def _similarity(source: Exercise, candidate: Exercise) -> float:
    score = 0.0
    if candidate.substitution_group == source.substitution_group:
        score += 0.55
    if candidate.movement_pattern == source.movement_pattern:
        score += 0.25
    shared_primary = set(source.primary_muscles) & set(candidate.primary_muscles)
    if shared_primary:
        score += 0.15
    if candidate.is_compound == source.is_compound:
        score += 0.05
    difficulty_gap = abs(candidate.difficulty - source.difficulty)
    score -= 0.03 * difficulty_gap
    return round(min(score, 0.99), 2)
