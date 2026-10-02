from __future__ import annotations

from pydantic import BaseModel

from app.rag.chunking import Chunk
from app.rag.embeddings import Embedder
from app.rag.store import InMemoryStore


class RetrieverConfig(BaseModel):
    chunk_size: int = 80
    overlap: int = 16
    top_k: int = 4
    fetch_k: int = 12
    hybrid: bool = True
    hybrid_alpha: float = 0.7
    rerank: bool = True
    contextual: bool = True
    topic: str | None = None
    audience: str | None = None


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float
    vector_score: float
    keyword_score: float


def retrieve(
    query: str,
    store: InMemoryStore,
    embedder: Embedder,
    config: RetrieverConfig,
) -> list[RetrievedChunk]:
    query_vector = embedder.embed([query])[0]
    fetch = max(config.top_k, config.fetch_k if config.rerank else config.top_k)
    raw = store.search(
        query_vector,
        top_k=max(fetch, store.size),
        topic=config.topic,
        audience=config.audience,
    )
    ranked: list[RetrievedChunk] = []
    for row, vector_score in raw:
        text = row.chunk.contextual_text if config.contextual else row.chunk.text
        keyword_score = _keyword_score(query, text)
        score = vector_score
        if config.hybrid:
            score = config.hybrid_alpha * vector_score + (1 - config.hybrid_alpha) * keyword_score
        ranked.append(
            RetrievedChunk(
                chunk=row.chunk,
                score=round(score, 4),
                vector_score=round(vector_score, 4),
                keyword_score=round(keyword_score, 4),
            )
        )
    ranked.sort(key=lambda item: item.score, reverse=True)
    if config.rerank:
        head = ranked[:fetch]
        head.sort(key=lambda item: (item.keyword_score, item.score), reverse=True)
        # blend: keep hybrid score but prefer keyword among the fetched set
        head.sort(
            key=lambda item: 0.6 * item.score + 0.4 * item.keyword_score,
            reverse=True,
        )
        ranked = head
    return ranked[: config.top_k]


def _keyword_score(query: str, text: str) -> float:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return 0.0
    text_tokens = set(_tokens(text))
    if not text_tokens:
        return 0.0
    overlap = query_tokens & text_tokens
    return len(overlap) / len(query_tokens)


def _tokens(text: str) -> list[str]:
    return [part for part in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if len(part) > 2]
