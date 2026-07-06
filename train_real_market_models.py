"""Train Phase 1 models on observed market outcomes."""

import argparse
import json

from data_layer.real_market_data import DEFAULT_REAL_DATA_TICKERS
from ml_models.real_market_trainer import RealMarketModelTrainer


def main():
    parser = argparse.ArgumentParser(description="Train leakage-aware real-market models.")
    parser.add_argument("--tickers", nargs="*", default=DEFAULT_REAL_DATA_TICKERS)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--rebuild-data", action="store_true")
    args = parser.parse_args()

    metrics = RealMarketModelTrainer().train(
        tickers=args.tickers,
        years=args.years,
        refresh=args.refresh,
        rebuild_data=args.rebuild_data,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
