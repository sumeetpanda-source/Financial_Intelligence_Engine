"""
Initialize Phase 1 local storage and cache the available US equity universe.
"""

import argparse

from config import get_settings
from data_layer.company_universe import USEquityUniverseBuilder
from storage import DataStore


def main():
    parser = argparse.ArgumentParser(description="Initialize storage and cache the US equity universe.")
    parser.add_argument("--fetch-remote", action="store_true", help="Download fresh Nasdaq/SEC universe source files.")
    parser.add_argument("--min-count", type=int, default=10000, help="Number of universe rows to cache.")
    args = parser.parse_args()

    settings = get_settings()
    store = DataStore(settings)
    directories = store.initialize()
    universe = USEquityUniverseBuilder(store).build(
        fetch_remote=args.fetch_remote,
        min_count=args.min_count,
    )

    print("Phase 1 storage initialized.")
    for name, path in directories.items():
        print(f"{name}: {path}")
    print(f"Cached US equity universe rows: {len(universe)}")
    if not args.fetch_remote and len(universe) < args.min_count:
        print("Run with --fetch-remote to download Nasdaq/SEC sources for the 10K-company universe.")


if __name__ == "__main__":
    main()
