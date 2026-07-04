"""
Retriever Agent.

Phase 1 uses local document loading plus TF-IDF retrieval. This is intentionally
simple and market-standard; the same interface can later be backed by FinBERT
embeddings and FAISS/Chroma/Pinecone.
"""

import os
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

from rag_layer.retriever import VectorRetriever as ChromaVectorRetriever

from .schemas import AgentResult, EvidenceItem


class RetrieverAgent:
    """Retrieves relevant local project/document chunks for a user query."""

    def __init__(
        self,
        chunk_size: int = 900,
        overlap: int = 120,
        retrieval_backend: Optional[str] = None,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.retrieval_backend = retrieval_backend or os.getenv("FIE_RETRIEVAL_BACKEND", "hybrid")

    def run(
        self,
        query: str,
        document_paths: Optional[Iterable[str]] = None,
        top_k: int = 5,
    ) -> AgentResult:
        vector_result = self._retrieve_from_vector_db(query, top_k=top_k)
        if vector_result is not None:
            return vector_result

        paths = [Path(path) for path in document_paths or []]
        chunks = self._load_chunks(paths)

        if not chunks:
            return AgentResult(
                agent_name="Retriever Agent",
                status="warning",
                summary="No documents were available for retrieval.",
                confidence=0.0,
                warnings=["Add filings, reports, news, or project documents to improve RAG."],
            )

        ranked = self._rank_chunks(query, chunks, top_k=top_k)
        evidence = [
            EvidenceItem(
                source=item["source"],
                text=item["text"],
                score=item["score"],
                metadata={"chunk_id": item["chunk_id"]},
            )
            for item in ranked
        ]

        return AgentResult(
            agent_name="Retriever Agent",
            status="success",
            summary=f"Retrieved {len(evidence)} relevant evidence chunks.",
            data={
                "retrieved_count": len(evidence),
                "corpus_chunks": len(chunks),
                "retrieval_backend": self.retrieval_backend,
                "retrieval_strategy": (
                    "Hybrid sparse retrieval: TF-IDF vector similarity + keyword overlap "
                    "+ source metadata boost. Optional semantic backend can be enabled later."
                ),
            },
            evidence=evidence,
            confidence=round(sum(item.score for item in evidence) / max(len(evidence), 1), 3),
        )

    def _retrieve_from_vector_db(self, query: str, top_k: int) -> AgentResult | None:
        try:
            retriever = ChromaVectorRetriever()
            if retriever.count() == 0:
                return None
            results = retriever.retrieve_similar(query, top_k=top_k)
        except Exception:
            return None

        evidence = [
            EvidenceItem(
                source=item.get("metadata", {}).get("source", "ChromaDB"),
                text=item.get("text", ""),
                score=item.get("score", 0.0),
                metadata={
                    **(item.get("metadata") or {}),
                    "vector_db": "ChromaDB",
                    "distance": item.get("distance"),
                },
            )
            for item in results
        ]
        return AgentResult(
            agent_name="Retriever Agent",
            status="success",
            summary=f"Retrieved {len(evidence)} evidence chunks from ChromaDB.",
            data={
                "retrieved_count": len(evidence),
                "corpus_chunks": retriever.count(),
                "retrieval_backend": "chromadb",
                "vector_db": "ChromaDB",
                "embedding_model": "local_hashing_embedder_384d",
                "retrieval_strategy": "hybrid vector + lexical + metadata reranking",
            },
            evidence=evidence,
            confidence=round(sum(item.score for item in evidence) / max(len(evidence), 1), 3),
        )

    def _load_chunks(self, paths: List[Path]) -> List[dict]:
        chunks = []
        for path in paths:
            if not path.exists() or path.is_dir():
                continue

            text = self._read_document(path)
            if not text:
                continue

            for chunk_id, chunk in enumerate(self._chunk_text(text)):
                chunks.append(
                    {
                        "source": str(path),
                        "chunk_id": chunk_id,
                        "text": chunk,
                    }
                )
        return chunks

    def _read_document(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                return ""

        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _chunk_text(self, text: str) -> List[str]:
        clean_text = " ".join(text.split())
        if not clean_text:
            return []

        step = max(self.chunk_size - self.overlap, 1)
        return [
            clean_text[start : start + self.chunk_size]
            for start in range(0, len(clean_text), step)
            if len(clean_text[start : start + self.chunk_size]) > 120
        ]

    def _rank_chunks(self, query: str, chunks: List[dict], top_k: int) -> List[dict]:
        texts = [chunk["text"] for chunk in chunks]
        tfidf_scores = self._tfidf_scores(query, texts)
        keyword_scores = np.array([self._keyword_overlap(query, text) for text in texts])
        metadata_scores = np.array([self._metadata_boost(query, chunk["source"]) for chunk in chunks])

        if self.retrieval_backend == "semantic":
            semantic_scores = self._semantic_scores(query, texts)
            scores = (
                semantic_scores * 0.60
                + tfidf_scores * 0.25
                + keyword_scores * 0.10
                + metadata_scores * 0.05
            )
        else:
            scores = (
                tfidf_scores * 0.70
                + keyword_scores * 0.20
                + metadata_scores * 0.10
            )

        ranked_indices = sorted(range(len(chunks)), key=lambda idx: scores[idx], reverse=True)[:top_k]
        ranked = []
        for idx in ranked_indices:
            item = dict(chunks[idx])
            item["score"] = round(float(scores[idx]), 4)
            item["score_components"] = {
                "tfidf": round(float(tfidf_scores[idx]), 4),
                "keyword": round(float(keyword_scores[idx]), 4),
                "metadata": round(float(metadata_scores[idx]), 4),
            }
            ranked.append(item)
        return ranked

    def _tfidf_scores(self, query: str, texts: List[str]) -> np.ndarray:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            matrix = vectorizer.fit_transform([query] + texts)
            return cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        except Exception:
            query_terms = {term.lower() for term in query.split() if len(term) > 2}
            scores = []
            for text in texts:
                text_lower = text.lower()
                scores.append(sum(1 for term in query_terms if term in text_lower) / max(len(query_terms), 1))
            return np.array(scores, dtype=float)

    def _semantic_scores(self, query: str, texts: List[str]) -> np.ndarray:
        """Optional dense embeddings. Requires a locally available model."""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            model_name = os.getenv("FIE_SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name)
            embeddings = model.encode([query] + texts, normalize_embeddings=True)
            return cosine_similarity([embeddings[0]], embeddings[1:]).flatten()
        except Exception:
            return self._tfidf_scores(query, texts)

    def _keyword_overlap(self, query: str, text: str) -> float:
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        if not query_terms:
            return 0.0
        text_lower = text.lower()
        return sum(1 for term in query_terms if term in text_lower) / len(query_terms)

    def _metadata_boost(self, query: str, source: str) -> float:
        source_lower = Path(source).name.lower()
        query_lower = query.lower()
        score = 0.0
        for token in ["summary", "rag", "data", "quick", "phase", "report", "executive"]:
            if token in query_lower and token in source_lower:
                score += 0.2
        return min(score, 1.0)
