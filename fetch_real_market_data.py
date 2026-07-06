"""Fetch and cache real Phase 1 market observations."""

import argparse
import json

from data_layer.real_market_data import DEFAULT_REAL_DATA_TICKERS, RealMarketDataPipeline


def main():
    parser = argparse.ArgumentParser(description="Fetch real OHLCV and company fundamentals.")
    parser.add_argument("--tickers", nargs="*", default=DEFAULT_REAL_DATA_TICKERS)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-fundamentals", action="store_true")
    args = parser.parse_args()

    result = RealMarketDataPipeline().run(
        tickers=args.tickers,
        years=args.years,
        refresh=args.refresh,
        include_fundamentals=not args.no_fundamentals,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
