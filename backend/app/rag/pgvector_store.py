from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.rag.chunking import Chunk
from app.rag.store import InMemoryStore, StoredChunk


class PgVectorStore:
    """Postgres + pgvector persistence. Search still uses the in-memory retriever after load."""

    def __init__(self, engine: Engine, dim: int):
        self.engine = engine
        self.dim = dim
        self._ensure()

    def _ensure(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS knowledge_chunks (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        audience TEXT NOT NULL,
                        body TEXT NOT NULL,
                        contextual_text TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        embedding vector({self.dim})
                    )
                    """
                )
            )

    def replace(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM knowledge_chunks"))
            for chunk, vector in zip(chunks, vectors, strict=True):
                conn.execute(
                    text(
                        """
                        INSERT INTO knowledge_chunks (
                            id, document_id, title, topic, audience, body,
                            contextual_text, chunk_index, embedding
                        ) VALUES (
                            :id, :document_id, :title, :topic, :audience, :body,
                            :contextual_text, :chunk_index, CAST(:embedding AS vector)
                        )
                        """
                    ),
                    {
                        "id": chunk.id,
                        "document_id": chunk.document_id,
                        "title": chunk.title,
                        "topic": chunk.topic,
                        "audience": chunk.audience,
                        "body": chunk.text,
                        "contextual_text": chunk.contextual_text,
                        "chunk_index": chunk.chunk_index,
                        "embedding": "[" + ",".join(f"{v:.6f}" for v in vector) + "]",
                    },
                )

    def load_memory(self) -> InMemoryStore:
        store = InMemoryStore()
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT id, document_id, title, topic, audience, body,
                           contextual_text, chunk_index, embedding::text
                    FROM knowledge_chunks
                    """
                )
            ).mappings()
            chunks: list[Chunk] = []
            vectors: list[list[float]] = []
            for row in rows:
                chunks.append(
                    Chunk(
                        id=row["id"],
                        document_id=row["document_id"],
                        title=row["title"],
                        topic=row["topic"],
                        audience=row["audience"],
                        text=row["body"],
                        contextual_text=row["contextual_text"],
                        chunk_index=row["chunk_index"],
                    )
                )
                vectors.append(_parse_vector(row["embedding"]))
            if chunks:
                store.add(chunks, vectors)
        return store


def _parse_vector(raw: str) -> list[float]:
    cleaned = raw.strip().removeprefix("[").removesuffix("]")
    if not cleaned:
        return []
    return [float(part) for part in cleaned.split(",")]
