from __future__ import annotations

from pydantic import BaseModel

from app.rag.documents import KnowledgeDocument


class Chunk(BaseModel):
    id: str
    document_id: str
    title: str
    topic: str
    audience: str
    text: str
    contextual_text: str
    chunk_index: int = 0


def chunk_documents(
    documents: list[KnowledgeDocument],
    *,
    chunk_size: int = 80,
    overlap: int = 16,
    contextual: bool = True,
) -> list[Chunk]:
    size = max(20, chunk_size)
    overlap = max(0, min(overlap, size - 1))
    chunks: list[Chunk] = []
    for document in documents:
        words = document.text.split()
        if not words:
            continue
        start = 0
        index = 0
        while start < len(words):
            end = min(len(words), start + size)
            piece = " ".join(words[start:end])
            prefix = f"Document: {document.title}. Topic: {document.topic}. "
            contextual_text = f"{prefix}{piece}" if contextual else piece
            chunks.append(
                Chunk(
                    id=f"{document.id}:{index}",
                    document_id=document.id,
                    title=document.title,
                    topic=document.topic,
                    audience=document.audience,
                    text=piece,
                    contextual_text=contextual_text,
                    chunk_index=index,
                )
            )
            if end == len(words):
                break
            start = end - overlap
            index += 1
    return chunks
