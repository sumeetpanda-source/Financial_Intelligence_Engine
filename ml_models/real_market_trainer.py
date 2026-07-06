"""Time-based training for the real-market Phase 1 baseline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd

from data_layer.real_market_data import RealMarketDataPipeline
from ml_models.phase1_trainer import Phase1ModelTrainer
from ml_models.price_predictor import PricePredictor
from ml_models.risk_scorer import RiskScorer
from storage import DataStore


class RealMarketModelTrainer(Phase1ModelTrainer):
    """Trains risk and direction models without random time leakage."""

    def __init__(self, store: DataStore | None = None):
        super().__init__(store=store)

    def train(
        self,
        tickers: Iterable[str] | None = None,
        years: int = 5,
        refresh: bool = False,
        rebuild_data: bool = False,
    ) -> dict:
        self.store.initialize()
        feature_path = (
            self.settings.feature_store_dir / RealMarketDataPipeline.TRAINING_FEATURE_FILE
        )
        if rebuild_data or not feature_path.exists():
            RealMarketDataPipeline(self.store).run(
                tickers=tickers,
                years=years,
                refresh=refresh,
            )

        features = pd.read_csv(feature_path)
        if features.empty or "feature_date" not in features:
            raise ValueError("Real market training features are missing or invalid.")

        train_frame, test_frame, split = self._time_split(features)
        risk_model = RiskScorer().train(train_frame)
        forecast_model = PricePredictor().train(train_frame)

        risk_metrics = self._evaluate_classifier(
            model=risk_model,
            test_frame=test_frame,
            target_column="risk_label",
        )
        forecast_metrics = self._evaluate_classifier(
            model=forecast_model,
            test_frame=test_frame,
            target_column="forecast_label",
        )

        self.settings.model_dir.mkdir(parents=True, exist_ok=True)
        risk_model_path = self.settings.model_dir / "phase1_risk_model.pkl"
        forecast_model_path = self.settings.model_dir / "phase1_forecast_model.pkl"
        metrics_path = self.settings.model_dir / "phase1_model_metrics.json"
        risk_model.save(risk_model_path)
        forecast_model.save(forecast_model_path)

        metrics = {
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "training_data_source": "real_yfinance_ohlcv",
            "split_strategy": "chronological_80_20",
            "feature_rows": int(len(features)),
            "ticker_count": int(features["ticker"].nunique()),
            "train_rows": int(len(train_frame)),
            "test_rows": int(len(test_frame)),
            "train_end_date": split["train_end_date"],
            "test_start_date": split["test_start_date"],
            "risk_label_contract": "Forward 20-day realized annualized volatility.",
            "forecast_label_contract": "Forward 20-day observed adjusted return.",
            "risk_model": {
                "artifact": str(risk_model_path),
                "algorithm": risk_model.model.__class__.__name__,
                **risk_metrics,
            },
            "forecast_model": {
                "artifact": str(forecast_model_path),
                "algorithm": forecast_model.model.__class__.__name__,
                **forecast_metrics,
            },
        }
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics

    @staticmethod
    def _time_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        dated = frame.copy()
        dated["feature_date"] = pd.to_datetime(dated["feature_date"], errors="coerce")
        dated = dated.dropna(subset=["feature_date"]).sort_values(["feature_date", "ticker"])
        unique_dates = dated["feature_date"].drop_duplicates().sort_values().tolist()
        if len(unique_dates) < 10:
            raise ValueError("At least 10 distinct feature dates are required for time-based training.")

        split_index = min(max(int(len(unique_dates) * 0.8), 1), len(unique_dates) - 1)
        split_date = unique_dates[split_index]
        train_frame = dated[dated["feature_date"] < split_date].copy()
        test_frame = dated[dated["feature_date"] >= split_date].copy()
        if train_frame.empty or test_frame.empty:
            raise ValueError("Chronological split produced an empty train or test set.")

        return train_frame, test_frame, {
            "train_end_date": train_frame["feature_date"].max().date().isoformat(),
            "test_start_date": test_frame["feature_date"].min().date().isoformat(),
        }
