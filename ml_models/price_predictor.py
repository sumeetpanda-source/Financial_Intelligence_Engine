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

from ml_models.simple_models import CentroidClassifier


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

    def __init__(self, model=None, feature_columns: Iterable[str] | None = None):
        self.model = model
        self.feature_columns = list(feature_columns or FORECAST_FEATURE_COLUMNS)

    def train(self, frame: pd.DataFrame):
        """Train a dependency-light centroid forecast classifier."""
        self.model = CentroidClassifier().fit(frame, self.feature_columns, "forecast_label")
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

    def save(self, path: str | Path):
        if self.model is None:
            raise ValueError("Forecast model is not trained.")
        payload = {"model": self.model, "feature_columns": self.feature_columns}
        with open(path, "wb") as file:
            pickle.dump(payload, file)

    @classmethod
    def load(cls, path: str | Path) -> "PricePredictor":
        with open(path, "rb") as file:
            payload = pickle.load(file)
        return cls(model=payload["model"], feature_columns=payload["feature_columns"])
