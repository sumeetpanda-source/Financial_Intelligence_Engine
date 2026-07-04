"""Tests for source-aware RAG chunk metadata."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rag_layer.document_loader import DocumentLoader
from rag_layer.retriever import VectorRetriever


def test_infer_metadata_for_financial_documents():
    metadata = DocumentLoader.infer_metadata(Path("AAPL_10-K_2025.pdf"))

    assert metadata["document_type"] == "10-K"
    assert metadata["year"] == 2025
    assert metadata["extension"] == ".pdf"


def test_text_chunks_include_source_metadata(tmp_path):
    document = tmp_path / "earnings_transcript_2026.txt"
    document.write_text("Revenue growth improved. " * 80, encoding="utf-8")

    chunks = DocumentLoader.load_chunks([document], chunk_size=300, overlap=50)

    assert chunks
    assert chunks[0]["metadata"]["document_type"] == "earnings"
    assert chunks[0]["metadata"]["year"] == 2026
    assert chunks[0]["metadata"]["source"] == str(document)


def test_hybrid_lexical_score_rewards_query_term_coverage():
    relevant = VectorRetriever._lexical_score(
        "phase one rag architecture",
        "The Phase One RAG architecture retrieves grounded evidence.",
    )
    unrelated = VectorRetriever._lexical_score(
        "phase one rag architecture",
        "Quarterly revenue and dividend growth improved.",
    )

    assert relevant > unrelated
