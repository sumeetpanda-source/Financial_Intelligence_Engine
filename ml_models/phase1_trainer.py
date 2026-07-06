"""
Phase 1 model training pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd

from data_layer.phase1_data_pipeline import Phase1DataPipeline
from ml_models.price_predictor import PricePredictor
from ml_models.risk_scorer import RiskScorer
from storage import DataStore


class Phase1ModelTrainer:
    """Trains baseline risk and forecast models for Phase 1."""

    def __init__(self, store: DataStore | None = None):
        self.store = store or DataStore()
        self.settings = self.store.settings

    def train(self, rebuild_features: bool = False, min_universe_count: int = 10000) -> Dict:
        self.store.initialize()
        feature_path = self.settings.feature_store_dir / Phase1DataPipeline.FEATURE_FILE
        if rebuild_features or not feature_path.exists():
            features = Phase1DataPipeline(self.store).build(min_universe_count=min_universe_count)
        else:
            features = pd.read_csv(feature_path)

        if features.empty:
            raise ValueError("No Phase 1 features available for model training.")

        train_frame, test_frame = self._split_train_test(features)

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

        risk_model_path = self.settings.model_dir / "phase1_risk_model.pkl"
        forecast_model_path = self.settings.model_dir / "phase1_forecast_model.pkl"
        metrics_path = self.settings.model_dir / "phase1_model_metrics.json"

        self.settings.model_dir.mkdir(parents=True, exist_ok=True)
        risk_model.save(risk_model_path)
        forecast_model.save(forecast_model_path)

        metrics = {
            "trained_at": datetime.utcnow().isoformat(),
            "feature_rows": int(len(features)),
            "train_rows": int(len(train_frame)),
            "test_rows": int(len(test_frame)),
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

    def _split_train_test(self, frame: pd.DataFrame):
        shuffled = frame.sample(frac=1.0, random_state=42).reset_index(drop=True)
        split_index = int(len(shuffled) * 0.8)
        return shuffled.iloc[:split_index].copy(), shuffled.iloc[split_index:].copy()

    def _evaluate_classifier(self, model, test_frame: pd.DataFrame, target_column: str) -> Dict:
        y_true = test_frame[target_column]
        y_pred = model.predict(test_frame)
        labels = sorted(y_true.astype(str).unique().tolist())
        report = self._classification_report(y_true.astype(str).tolist(), y_pred, labels)
        majority_label = y_true.astype(str).value_counts().idxmax()
        majority_accuracy = float((y_true.astype(str) == majority_label).mean())
        random_balanced_baseline = 1.0 / len(labels) if labels else 0.0
        return {
            "accuracy": report["accuracy"],
            "balanced_accuracy": report["balanced_accuracy"],
            "macro_f1": report["macro_f1"],
            "weighted_f1": report["weighted_f1"],
            "majority_baseline_label": majority_label,
            "majority_baseline_accuracy": round(majority_accuracy, 4),
            "accuracy_lift_vs_majority": round(report["accuracy"] - majority_accuracy, 4),
            "balanced_accuracy_lift_vs_random": round(
                report["balanced_accuracy"] - random_balanced_baseline,
                4,
            ),
            "classification_report": report["by_label"],
        }

    def _classification_report(self, y_true, y_pred, labels) -> Dict:
        by_label = {}
        total = len(y_true)
        correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
        weighted_f1_sum = 0.0
        macro_f1_values = []
        recall_values = []

        for label in labels:
            tp = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred == label)
            fp = sum(1 for true, pred in zip(y_true, y_pred) if true != label and pred == label)
            fn = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred != label)
            support = sum(1 for true in y_true if true == label)
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            weighted_f1_sum += f1 * support
            macro_f1_values.append(f1)
            recall_values.append(recall)
            by_label[label] = {
                "precision": round(float(precision), 4),
                "recall": round(float(recall), 4),
                "f1_score": round(float(f1), 4),
                "support": int(support),
            }

        return {
            "accuracy": round(float(correct / total if total else 0), 4),
            "balanced_accuracy": round(
                float(sum(recall_values) / len(recall_values) if recall_values else 0),
                4,
            ),
            "macro_f1": round(float(sum(macro_f1_values) / len(macro_f1_values) if macro_f1_values else 0), 4),
            "weighted_f1": round(float(weighted_f1_sum / total if total else 0), 4),
            "by_label": by_label,
        }


if __name__ == "__main__":
    metrics = Phase1ModelTrainer().train()
    print(json.dumps(metrics, indent=2))
