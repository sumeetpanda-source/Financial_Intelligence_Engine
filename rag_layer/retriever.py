"""
Chroma vector database retriever for Phase 1 RAG.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List

import chromadb

from config import get_settings
from rag_layer.embeddings import HashingEmbedder


class VectorRetriever:
    """Persistent Chroma retriever with local deterministic embeddings."""

    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
        "to", "what", "with",
    }

    def __init__(self, collection_name: str = "phase1_financial_docs", persist_dir: str | Path | None = None):
        settings = get_settings()
        self.persist_dir = Path(persist_dir or settings.vector_store_dir / "chroma")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = HashingEmbedder()
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Phase 1 financial RAG document chunks"},
        )

    def reset(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Phase 1 financial RAG document chunks"},
        )

    def count(self) -> int:
        return int(self.collection.count())

    def store_documents(self, chunks: Iterable[Dict], reset: bool = False) -> int:
        chunks = list(chunks)
        if reset:
            self.reset()
        if not chunks:
            return self.count()

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        embeddings = self.embedder.embed_batch(documents)

        batch_size = 500
        for start in range(0, len(chunks), batch_size):
            end = start + batch_size
            self.collection.upsert(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end],
            )
        return self.count()

    def retrieve_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.count() == 0:
            return []

        query_embedding = self.embedder.embed_text(query)
        candidate_count = min(self.count(), max(top_k * 20, 2000))
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
        )

        rows = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            vector_score = 1.0 / (1.0 + max(float(distance), 0.0))
            lexical_score = self._lexical_score(query, document)
            metadata_score = self._metadata_score(query, metadata or {})
            score = vector_score * 0.55 + lexical_score * 0.35 + metadata_score * 0.10
            rows.append(
                {
                    "id": item_id,
                    "text": document,
                    "metadata": metadata or {},
                    "score": round(score, 4),
                    "distance": round(float(distance), 4),
                    "score_components": {
                        "vector": round(vector_score, 4),
                        "lexical": round(lexical_score, 4),
                        "metadata": round(metadata_score, 4),
                    },
                }
            )
        return sorted(rows, key=lambda item: item["score"], reverse=True)[:top_k]

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(token) > 1 and token not in cls.STOP_WORDS
        }

    @classmethod
    def _lexical_score(cls, query: str, document: str) -> float:
        query_tokens = cls._tokens(query)
        if not query_tokens:
            return 0.0
        document_tokens = cls._tokens(document)
        overlap = len(query_tokens & document_tokens) / len(query_tokens)
        phrase_bonus = 0.15 if query.lower().strip() in document.lower() else 0.0
        return min(overlap + phrase_bonus, 1.0)

    @classmethod
    def _metadata_score(cls, query: str, metadata: Dict) -> float:
        query_tokens = cls._tokens(query)
        if not query_tokens:
            return 0.0
        searchable = " ".join(
            str(metadata.get(field, ""))
            for field in (
                "ticker",
                "company_name",
                "filename",
                "source",
                "document_type",
                "filing_date",
                "year",
            )
        )
        metadata_tokens = cls._tokens(searchable)
        return len(query_tokens & metadata_tokens) / len(query_tokens)
