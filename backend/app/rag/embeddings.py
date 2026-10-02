from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.config import settings


TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic sparse-hashed bag of words. No API key, tests stay offline."""

    name = "hash"

    def __init__(self, dim: int = 96):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_vector(text, self.dim) for text in texts]


class OpenAIEmbedder:
    name = "openai"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dim: int = 1536):
        from openai import OpenAI

        self.dim = dim
        self.model = model
        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


def build_embedder() -> Embedder:
    provider = (settings.embedding_provider or "hash").strip().lower()
    key = (settings.openai_api_key or "").strip()
    if provider == "openai" and key:
        return OpenAIEmbedder(api_key=key)
    return HashingEmbedder(dim=settings.embedding_dim)


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    return max(-1.0, min(1.0, dot))


def _vector(text: str, dim: int) -> list[float]:
    values = [0.0] * dim
    tokens = TOKEN.findall(text.lower())
    grams = tokens + [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
    for token in grams:
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        values[index] += sign
    return _normalize(values)


def _normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]
