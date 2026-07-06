"""
Document loader for Phase 1 RAG.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


class DocumentLoader:
    """Loads and chunks financial documents."""

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".pdf"}

    @staticmethod
    def load_pdf_pages(filepath: str | Path) -> List[Dict]:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(filepath))
            return [
                {"page_number": index, "text": page.extract_text() or ""}
                for index, page in enumerate(reader.pages, start=1)
            ]
        except Exception:
            return []

    @classmethod
    def load_pdf(cls, filepath: str | Path) -> str:
        pages = cls.load_pdf_pages(filepath)
        if not pages:
            return ""
        return "\n".join(page["text"] for page in pages)

    @staticmethod
    def load_text(filepath: str | Path) -> str:
        try:
            return Path(filepath).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    @classmethod
    def load_document(cls, filepath: str | Path) -> str:
        path = Path(filepath)
        if path.suffix.lower() == ".pdf":
            return cls.load_pdf(path)
        return cls.load_text(path)

    @classmethod
    def collect_documents(cls, paths: Iterable[str | Path]) -> List[Path]:
        documents: List[Path] = []
        for item in paths:
            path = Path(item)
            if (
                path.is_file()
                and path.suffix.lower() in cls.SUPPORTED_EXTENSIONS
                and not path.name.endswith(".metadata.json")
                and path.name != "ingestion_manifest.json"
            ):
                documents.append(path)
            elif path.is_dir():
                for child in path.rglob("*"):
                    if (
                        child.is_file()
                        and child.suffix.lower() in cls.SUPPORTED_EXTENSIONS
                        and not child.name.endswith(".metadata.json")
                        and child.name != "ingestion_manifest.json"
                    ):
                        documents.append(child)
        return sorted(set(documents))

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
        clean_text = " ".join((text or "").split())
        if not clean_text:
            return []

        step = max(chunk_size - overlap, 1)
        return [
            clean_text[start : start + chunk_size]
            for start in range(0, len(clean_text), step)
            if len(clean_text[start : start + chunk_size]) > 120
        ]

    @staticmethod
    def infer_metadata(document: Path) -> Dict:
        filename = document.name
        normalized = filename.lower().replace("_", "-")
        if re.search(r"\b10-?k\b", normalized):
            document_type = "10-K"
        elif re.search(r"\b10-?q\b", normalized):
            document_type = "10-Q"
        elif "earning" in normalized or "transcript" in normalized:
            document_type = "earnings"
        elif "annual" in normalized:
            document_type = "annual-report"
        elif document.suffix.lower() == ".pdf":
            document_type = "research-paper"
        elif document.suffix.lower() in {".csv", ".json"}:
            document_type = "structured-data"
        else:
            document_type = "project-document"

        metadata: Dict[str, str | int] = {
            "source": str(document),
            "filename": filename,
            "extension": document.suffix.lower(),
            "document_type": document_type,
        }
        year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", filename)
        if year_match:
            metadata["year"] = int(year_match.group(1))
        ticker_match = re.match(r"^([A-Z]{1,5})[_-]", filename)
        if ticker_match:
            metadata["ticker"] = ticker_match.group(1)

        sidecar = document.with_suffix(document.suffix + ".metadata.json")
        if sidecar.exists():
            try:
                extra = json.loads(sidecar.read_text(encoding="utf-8"))
                metadata.update(
                    {
                        str(key): value
                        for key, value in extra.items()
                        if isinstance(value, (str, int, float, bool))
                    }
                )
            except (OSError, ValueError, TypeError):
                pass
        return metadata

    @classmethod
    def load_chunks(cls, paths: Iterable[str | Path], chunk_size: int = 900, overlap: int = 120) -> List[Dict]:
        chunks = []
        for document in cls.collect_documents(paths):
            base_metadata = cls.infer_metadata(document)
            if document.suffix.lower() == ".pdf":
                text_units = cls.load_pdf_pages(document)
            else:
                text_units = [{"page_number": None, "text": cls.load_document(document)}]

            document_chunk_id = 0
            for unit in text_units:
                page_number = unit["page_number"]
                page_chunks = cls.chunk_text(unit["text"], chunk_size=chunk_size, overlap=overlap)
                for page_chunk_id, chunk in enumerate(page_chunks):
                    metadata = {
                        **base_metadata,
                        "chunk_id": document_chunk_id,
                    }
                    if page_number is not None:
                        metadata["page_number"] = int(page_number)
                        metadata["page_chunk_id"] = page_chunk_id

                    page_label = f"page-{page_number}" if page_number is not None else "document"
                    chunks.append(
                        {
                            "id": f"{document.as_posix()}::{page_label}::{page_chunk_id}",
                            "text": chunk,
                            "metadata": metadata,
                        }
                    )
                    document_chunk_id += 1
        return chunks
