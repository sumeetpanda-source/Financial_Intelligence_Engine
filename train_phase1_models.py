"""
Train Phase 1 baseline ML models.
"""

import argparse
import json

from ml_models.phase1_trainer import Phase1ModelTrainer


def main():
    parser = argparse.ArgumentParser(description="Train Phase 1 risk and forecast models.")
    parser.add_argument("--rebuild-features", action="store_true", help="Rebuild feature dataset before training.")
    parser.add_argument("--min-count", type=int, default=10000, help="Universe size target when rebuilding features.")
    args = parser.parse_args()

    metrics = Phase1ModelTrainer().train(
        rebuild_features=args.rebuild_features,
        min_universe_count=args.min_count,
    )
    print(json.dumps(metrics, indent=2))
    print("Saved: models/phase1_risk_model.pkl")
    print("Saved: models/phase1_forecast_model.pkl")
    print("Saved: models/phase1_model_metrics.json")


if __name__ == "__main__":
    main()
