from __future__ import annotations

from dataclasses import dataclass, field

from app.rag.chunking import Chunk
from app.rag.embeddings import cosine


@dataclass
class StoredChunk:
    chunk: Chunk
    vector: list[float]


class InMemoryStore:
    def __init__(self) -> None:
        self._rows: list[StoredChunk] = []

    def clear(self) -> None:
        self._rows = []

    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self._rows.append(StoredChunk(chunk=chunk, vector=vector))

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int,
        topic: str | None = None,
        audience: str | None = None,
    ) -> list[tuple[StoredChunk, float]]:
        scored: list[tuple[StoredChunk, float]] = []
        for row in self._rows:
            if topic and row.chunk.topic != topic:
                continue
            if audience and row.chunk.audience not in {audience, "all"}:
                continue
            scored.append((row, cosine(query_vector, row.vector)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(1, top_k)]

    @property
    def size(self) -> int:
        return len(self._rows)

    def all_rows(self) -> list[StoredChunk]:
        return list(self._rows)
