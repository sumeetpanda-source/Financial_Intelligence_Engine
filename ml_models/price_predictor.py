"""
Forecast model for Phase 1.

The Phase 1 baseline predicts 30-day direction classes: Down, Flat, Up. This is
fast and explainable. A PyTorch LSTM can later be added while preserving the
same agent-facing output.
"""

from __future__ import annotations

from pathlib import Path
import pickle
from typing import Iterable, List

import pandas as pd

from ml_models.simple_models import build_tabular_classifier


FORECAST_FEATURE_COLUMNS = [
    "daily_return_20d",
    "momentum_30d",
    "volatility_20",
    "volatility_60",
    "volume_ratio",
    "rsi_14",
    "sentiment_score",
    "liquidity_score",
]


class PricePredictor:
    """Trainable 30-day forecast direction classifier."""

    def __init__(
        self,
        model=None,
        feature_columns: Iterable[str] | None = None,
        class_return_means: dict[str, float] | None = None,
    ):
        self.model = model
        self.feature_columns = list(feature_columns or FORECAST_FEATURE_COLUMNS)
        self.class_return_means = class_return_means or {
            "Down": -0.05,
            "Flat": 0.0,
            "Up": 0.05,
        }

    def train(self, frame: pd.DataFrame):
        """Train a class-balanced direction classifier with a NumPy fallback."""
        self.model = build_tabular_classifier().fit(
            frame,
            self.feature_columns,
            "forecast_label",
        )
        if "future_return_30d" in frame:
            observed = (
                frame.groupby("forecast_label")["future_return_30d"]
                .mean()
                .dropna()
                .to_dict()
            )
            self.class_return_means.update(
                {str(label): float(value) for label, value in observed.items()}
            )
        return self

    def predict(self, frame: pd.DataFrame) -> List[str]:
        if self.model is None:
            raise ValueError("Forecast model is not trained or loaded.")
        return list(self.model.predict(frame[self.feature_columns]))

    def predict_proba(self, frame: pd.DataFrame):
        if self.model is None:
            raise ValueError("Forecast model is not trained or loaded.")
        labels = self.model.labels
        probabilities = self.model.predict_proba(frame[self.feature_columns])
        return labels, probabilities

    def expected_return(self, frame: pd.DataFrame) -> List[float]:
        labels, probabilities = self.predict_proba(frame)
        return [
            float(
                sum(
                    probability * self.class_return_means.get(label, 0.0)
                    for label, probability in zip(labels, row)
                )
            )
            for row in probabilities
        ]

    def save(self, path: str | Path):
        if self.model is None:
            raise ValueError("Forecast model is not trained.")
        payload = {
            "model": self.model,
            "feature_columns": self.feature_columns,
            "class_return_means": self.class_return_means,
        }
        with open(path, "wb") as file:
            pickle.dump(payload, file)

    @classmethod
    def load(cls, path: str | Path) -> "PricePredictor":
        with open(path, "rb") as file:
            payload = pickle.load(file)
        return cls(
            model=payload["model"],
            feature_columns=payload["feature_columns"],
            class_return_means=payload.get("class_return_means"),
        )
