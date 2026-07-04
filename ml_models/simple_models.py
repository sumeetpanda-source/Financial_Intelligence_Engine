"""
Small NumPy-based classifiers for dependency-light Phase 1 training.
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np
import pandas as pd


class CentroidClassifier:
    """Nearest-centroid classifier with standardized numeric features."""

    def __init__(self):
        self.feature_columns: List[str] = []
        self.labels: List[str] = []
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None
        self.centroids_: dict[str, np.ndarray] = {}

    def fit(self, frame: pd.DataFrame, feature_columns: Iterable[str], target_column: str):
        self.feature_columns = list(feature_columns)
        X = frame[self.feature_columns].astype(float).to_numpy()
        y = frame[target_column].astype(str).to_numpy()
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ == 0] = 1.0

        X_scaled = self._scale(X)
        self.labels = sorted(pd.Series(y).dropna().unique().tolist())
        self.centroids_ = {
            label: X_scaled[y == label].mean(axis=0)
            for label in self.labels
        }
        return self

    def predict(self, frame: pd.DataFrame) -> List[str]:
        probabilities = self.predict_proba(frame)
        label_indexes = probabilities.argmax(axis=1)
        return [self.labels[index] for index in label_indexes]

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        if self.mean_ is None or self.std_ is None or not self.centroids_:
            raise ValueError("CentroidClassifier has not been fitted.")

        X = frame[self.feature_columns].astype(float).to_numpy()
        X_scaled = self._scale(X)
        distances = []
        for label in self.labels:
            centroid = self.centroids_[label]
            distances.append(np.linalg.norm(X_scaled - centroid, axis=1))

        distance_matrix = np.vstack(distances).T
        scores = np.exp(-distance_matrix)
        score_sum = scores.sum(axis=1, keepdims=True)
        score_sum[score_sum == 0] = 1.0
        return scores / score_sum

    def _scale(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.std_
