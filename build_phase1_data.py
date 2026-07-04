"""
Build large-universe Phase 1 feature artifacts.
"""

import argparse

from data_layer.phase1_data_pipeline import Phase1DataPipeline


def main():
    parser = argparse.ArgumentParser(description="Build Phase 1 large-universe feature dataset.")
    parser.add_argument("--min-count", type=int, default=10000, help="Number of US equity universe rows to cache.")
    parser.add_argument("--fetch-remote", action="store_true", help="Download fresh Nasdaq/SEC universe source files.")
    args = parser.parse_args()

    features = Phase1DataPipeline().build(
        min_universe_count=args.min_count,
        fetch_remote_universe=args.fetch_remote,
    )
    print(f"Generated Phase 1 features: {len(features)} rows x {len(features.columns)} columns")
    print("Saved: data/features/phase1_model_features.csv")
    print("Saved: data/processed/phase1_data_pipeline_summary.json")


if __name__ == "__main__":
    main()
