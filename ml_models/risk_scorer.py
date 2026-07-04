"""
Risk scoring model for Phase 1.

Uses a scikit-learn pipeline by default so training is fast and reliable in a
local college-project environment. TensorFlow can be added later behind the same
predict contract.
"""

from __future__ import annotations

from pathlib import Path
import pickle
from typing import Iterable, List

import pandas as pd

from ml_models.simple_models import CentroidClassifier


RISK_FEATURE_COLUMNS = [
    "daily_return_20d",
    "momentum_30d",
    "volatility_20",
    "volatility_60",
    "max_drawdown",
    "volume_ratio",
    "rsi_14",
    "leverage_proxy",
    "sentiment_score",
    "liquidity_score",
]


class RiskScorer:
    """Trainable Low/Medium/High risk classifier."""

    def __init__(self, model=None, feature_columns: Iterable[str] | None = None):
        self.model = model
        self.feature_columns = list(feature_columns or RISK_FEATURE_COLUMNS)

    def train(self, frame: pd.DataFrame):
        """Train a dependency-light centroid risk classifier."""
        self.model = CentroidClassifier().fit(frame, self.feature_columns, "risk_label")
        return self

    def predict(self, frame: pd.DataFrame) -> List[str]:
        if self.model is None:
            raise ValueError("Risk model is not trained or loaded.")
        return list(self.model.predict(frame[self.feature_columns]))

    def predict_proba(self, frame: pd.DataFrame):
        if self.model is None:
            raise ValueError("Risk model is not trained or loaded.")
        labels = self.model.labels
        probabilities = self.model.predict_proba(frame[self.feature_columns])
        return labels, probabilities

    def save(self, path: str | Path):
        if self.model is None:
            raise ValueError("Risk model is not trained.")
        payload = {"model": self.model, "feature_columns": self.feature_columns}
        with open(path, "wb") as file:
            pickle.dump(payload, file)

    @classmethod
    def load(cls, path: str | Path) -> "RiskScorer":
        with open(path, "rb") as file:
            payload = pickle.load(file)
        return cls(model=payload["model"], feature_columns=payload["feature_columns"])
