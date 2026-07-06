"""Prepare the best available Phase 1 model artifacts during a cloud build."""

from __future__ import annotations

import json

from data_layer.real_market_data import DEFAULT_REAL_DATA_TICKERS, RealMarketDataPipeline
from ml_models.phase1_trainer import Phase1ModelTrainer
from ml_models.real_market_trainer import RealMarketModelTrainer
from storage import DataStore


def main():
    store = DataStore()
    store.initialize()
    result = {}
    try:
        real_summary = RealMarketDataPipeline(store).run(
            tickers=DEFAULT_REAL_DATA_TICKERS,
            years=5,
            refresh=True,
            include_fundamentals=True,
        )
        metrics = RealMarketModelTrainer(store).train()
        result = {
            "status": "real_market_models_ready",
            "real_market": real_summary,
            "model_metrics": metrics,
        }
    except Exception as exc:
        metrics = Phase1ModelTrainer(store).train()
        result = {
            "status": "proxy_model_fallback",
            "warning": str(exc),
            "model_metrics": metrics,
        }

    store.save_json("processed", "cloud_model_preparation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
