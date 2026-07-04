"""
Index Phase 1 documents into the local Chroma vector database.
"""

import argparse
import sys
from pathlib import Path

from rag_layer.rag_system import RAGSystem

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def default_paths(project_root: Path):
    return [
        project_root / "README.md",
        project_root / "docs",
        project_root / "reports",
    ]


def main():
    parser = argparse.ArgumentParser(description="Index Phase 1 RAG documents into ChromaDB.")
    parser.add_argument("paths", nargs="*", help="Files or directories to index.")
    parser.add_argument("--no-reset", action="store_true", help="Append/update instead of recreating the collection.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    paths = [Path(path) for path in args.paths] if args.paths else default_paths(project_root)
    result = RAGSystem().index_documents(paths, reset=not args.no_reset)
    print("Phase 1 RAG index complete.")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
