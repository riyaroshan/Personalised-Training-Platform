from __future__ import annotations

from pydantic import BaseModel

from app.rag.index import KnowledgeIndex, get_index
from app.rag.retrieve import RetrieverConfig, RetrievedChunk


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    topic: str
    text: str
    score: float


class RagAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    retriever: RetrieverConfig
    source: str


def answer_question(
    question: str,
    *,
    config: RetrieverConfig | None = None,
    index: KnowledgeIndex | None = None,
) -> RagAnswer:
    index = index or get_index()
    config = config or index.config
    hits = index.search(question, config)
    citations = [
        Citation(
            chunk_id=hit.chunk.id,
            document_id=hit.chunk.document_id,
            title=hit.chunk.title,
            topic=hit.chunk.topic,
            text=hit.chunk.text,
            score=hit.score,
        )
        for hit in hits
    ]
    return RagAnswer(
        answer=_extractive_answer(question, hits),
        citations=citations,
        retriever=config,
        source="rag_extractive",
    )


def ablate(question: str, index: KnowledgeIndex | None = None) -> list[dict]:
    index = index or get_index()
    variants = [
        RetrieverConfig(hybrid=False, rerank=False, top_k=3, chunk_size=80, contextual=True),
        RetrieverConfig(hybrid=True, rerank=False, top_k=3, chunk_size=80, contextual=True),
        RetrieverConfig(hybrid=True, rerank=True, top_k=3, chunk_size=80, contextual=True),
        RetrieverConfig(hybrid=True, rerank=True, top_k=3, chunk_size=40, contextual=True),
        RetrieverConfig(hybrid=True, rerank=True, top_k=3, chunk_size=80, contextual=False),
        RetrieverConfig(hybrid=True, rerank=True, top_k=3, chunk_size=80, topic="injury"),
    ]
    reports = []
    for config in variants:
        hits = index.search(question, config)
        reports.append(
            {
                "settings": config.model_dump(),
                "top_document_ids": [hit.chunk.document_id for hit in hits],
                "top_scores": [hit.score for hit in hits],
                "top_titles": [hit.chunk.title for hit in hits],
            }
        )
    return reports


def _extractive_answer(question: str, hits: list[RetrievedChunk]) -> str:
    if not hits:
        return "No passages were retrieved for that question."
    lines = [
        f"Question: {question}",
        "Answer grounded in retrieved passages:",
    ]
    for hit in hits[:3]:
        lines.append(f"- [{hit.chunk.document_id}] {hit.chunk.title}: {hit.chunk.text}")
    return "\n".join(lines)
