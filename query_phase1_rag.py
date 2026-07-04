"""
Ask a question against the Phase 1 RAG index.
"""

import argparse
import sys

from rag_layer.rag_system import RAGSystem

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Query the Phase 1 RAG system.")
    parser.add_argument("question", nargs="?", default="What is implemented in Phase 1?")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    result = RAGSystem().query(args.question, top_k=args.top_k)
    print(result["answer"])
    print("\nSources:")
    for idx, item in enumerate(result["evidence"], start=1):
        metadata = item.get("metadata", {})
        page = metadata.get("page_number")
        location = f" page={page}" if page else ""
        print(
            f"{idx}. {metadata.get('source')}{location} "
            f"score={item.get('score')} components={item.get('score_components', {})}"
        )


if __name__ == "__main__":
    main()
