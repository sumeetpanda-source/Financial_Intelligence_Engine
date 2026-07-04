"""
Complete Phase 1 RAG system.

RAG flow:
documents -> chunks -> embeddings -> Chroma vector DB -> retrieval -> LLM/fallback answer
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from genai_layer import build_genai_provider
from rag_layer.document_loader import DocumentLoader
from rag_layer.retriever import VectorRetriever


class RAGSystem:
    """Retrieval-Augmented Generation system for financial analysis."""

    def __init__(self, collection_name: str = "phase1_financial_docs"):
        self.loader = DocumentLoader()
        self.retriever = VectorRetriever(collection_name=collection_name)
        self.llm = build_genai_provider()

    def index_documents(self, document_paths: Iterable[str | Path], reset: bool = True) -> dict:
        chunks = self.loader.load_chunks(document_paths)
        count = self.retriever.store_documents(chunks, reset=reset)
        return {
            "indexed_chunks": len(chunks),
            "vector_db": "ChromaDB",
            "collection": self.retriever.collection_name,
            "collection_count": count,
            "embedding_model": "local_hashing_embedder_384d",
            "retrieval_strategy": "hybrid_vector_lexical_metadata_reranking",
        }

    def retrieve(self, question: str, top_k: int = 5) -> List[dict]:
        return self.retriever.retrieve_similar(question, top_k=top_k)

    def query(self, question: str, top_k: int = 5) -> dict:
        evidence = self.retrieve(question, top_k=top_k)
        answer = self._answer_with_context(question, evidence)
        return {
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "vector_db": "ChromaDB",
            "llm_provider": self.llm.__class__.__name__,
        }

    def _answer_with_context(self, question: str, evidence: List[dict]) -> str:
        if not evidence:
            return (
                "No indexed evidence was found. Run `python index_phase1_rag.py` "
                "before asking RAG questions."
            )

        context_lines = []
        for idx, item in enumerate(evidence, start=1):
            metadata = item.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page_number")
            location = f", page {page}" if page else ""
            context_lines.append(
                f"[{idx}] Source: {source}{location}\n"
                f"Relevance: {item.get('score', 0)}\n"
                f"Text: {item.get('text', '')[:900]}"
            )

        prompt = (
            "You are the RAG answer layer for a financial intelligence engine.\n"
            "Answer only from the provided evidence. If evidence is weak, say so.\n\n"
            f"Question:\n{question}\n\n"
            "Evidence:\n"
            + "\n\n".join(context_lines)
            + "\n\nAnswer with concise bullets and cite evidence numbers like [1]."
        )

        generated = self.llm.generate_report(prompt)
        if generated == prompt:
            return self._local_extractive_answer(question, evidence)
        return generated

    def _local_extractive_answer(self, question: str, evidence: List[dict]) -> str:
        lines = [
            "Local LLM fallback answer:",
            f"- Question: {question}",
            "- Best available evidence:",
        ]
        for idx, item in enumerate(evidence[:3], start=1):
            metadata = item.get("metadata", {})
            source = metadata.get("source", "unknown")
            page = metadata.get("page_number")
            location = f", page {page}" if page else ""
            snippet = item.get("text", "")[:280].strip()
            lines.append(f"  - [{idx}] {snippet} (source: {source}{location})")
        lines.append("- Note: This is extractive RAG output. Configure an LLM provider for abstractive synthesis.")
        return "\n".join(lines)
