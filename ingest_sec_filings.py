"""Download SEC filings and append them to the Phase 1 Chroma index."""

import argparse
import json
from pathlib import Path

from rag_layer.rag_system import RAGSystem
from rag_layer.sec_filings import SECFilingIngestor


def main():
    parser = argparse.ArgumentParser(description="Ingest SEC 10-K/10-Q filings into RAG.")
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "NVDA"])
    parser.add_argument("--forms", nargs="+", default=["10-K", "10-Q"])
    parser.add_argument("--per-form", type=int, default=1)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--skip-index", action="store_true")
    args = parser.parse_args()

    result = SECFilingIngestor().ingest(
        tickers=args.tickers,
        forms=args.forms,
        per_form=args.per_form,
        refresh=args.refresh,
    )
    if not args.skip_index and result["downloaded"]:
        paths = [Path(item["local_path"]) for item in result["downloaded"]]
        result["rag_index"] = RAGSystem().index_documents(paths, reset=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
