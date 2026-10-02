from __future__ import annotations

from app.config import settings
from app.rag.chunking import chunk_documents
from app.rag.documents import DOCUMENTS
from app.rag.embeddings import Embedder, build_embedder
from app.rag.retrieve import RetrieverConfig, RetrievedChunk, retrieve
from app.rag.store import InMemoryStore


class KnowledgeIndex:
    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or build_embedder()
        self.store = InMemoryStore()
        self.config = RetrieverConfig(
            chunk_size=settings.rag_chunk_size,
            overlap=settings.rag_chunk_overlap,
            top_k=settings.rag_top_k,
            contextual=True,
            hybrid=True,
            rerank=True,
        )
        self.rebuild(self.config)

    def rebuild(self, config: RetrieverConfig) -> None:
        self.config = config
        self.store = self._build_store(config)
        if settings.database_url.startswith("postgresql"):
            chunks = chunk_documents(
                DOCUMENTS,
                chunk_size=config.chunk_size,
                overlap=config.overlap,
                contextual=config.contextual,
            )
            vectors = self.embedder.embed(
                [chunk.contextual_text if config.contextual else chunk.text for chunk in chunks]
            )
            self._persist_postgres(chunks, vectors)

    def search(self, query: str, config: RetrieverConfig | None = None) -> list[RetrievedChunk]:
        active = config or self.config
        store = self.store
        if (
            active.chunk_size != self.config.chunk_size
            or active.overlap != self.config.overlap
            or active.contextual != self.config.contextual
        ):
            store = self._build_store(active)
        return retrieve(query, store, self.embedder, active)

    def _build_store(self, config: RetrieverConfig) -> InMemoryStore:
        chunks = chunk_documents(
            DOCUMENTS,
            chunk_size=config.chunk_size,
            overlap=config.overlap,
            contextual=config.contextual,
        )
        vectors = self.embedder.embed(
            [chunk.contextual_text if config.contextual else chunk.text for chunk in chunks]
        )
        store = InMemoryStore()
        store.add(chunks, vectors)
        return store

    def _persist_postgres(self, chunks, vectors) -> None:
        try:
            from app.db import engine
            from app.rag.pgvector_store import PgVectorStore

            PgVectorStore(engine, dim=self.embedder.dim).replace(chunks, vectors)
        except Exception:
            return


_INDEX: KnowledgeIndex | None = None


def get_index() -> KnowledgeIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = KnowledgeIndex()
    return _INDEX
