"""
Embedding providers for Phase 1 RAG.

Phase 1 uses a deterministic hashing embedder by default. It is local, fast,
dependency-light, and stable for demos. Transformer/FinBERT embeddings can be
added later behind the same interface.
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable, List

import numpy as np


class HashingEmbedder:
    """Create fixed-size normalized vectors from text using token hashing."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed_text(self, text: str) -> List[float]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = re.findall(r"[A-Za-z0-9_.$%-]+", text.lower())
        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimensions
            sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
            vector[index] += sign

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.astype(float).tolist()

    def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        return [self.embed_text(text) for text in texts]


class FinBERTEmbedder:
    """
    Placeholder-compatible FinBERT embedder.

    Uses local hashing unless a transformer implementation is added later. This
    keeps existing imports stable while avoiding runtime model downloads.
    """

    def __init__(self, dimensions: int = 384):
        self.fallback = HashingEmbedder(dimensions=dimensions)

    def embed_text(self, text: str) -> List[float]:
        return self.fallback.embed_text(text)

    def embed_batch(self, texts: Iterable[str]) -> List[List[float]]:
        return self.fallback.embed_batch(texts)
