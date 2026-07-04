"""
Local-first storage manager.

The directory layout mirrors what we will later use in cloud object storage:
raw inputs, processed data, features, vectors, models, and reports.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from config import AppSettings, get_settings


class DataStore:
    """Persists Phase 1 artifacts in an examiner-friendly layout."""

    def __init__(self, settings: AppSettings | None = None):
        self.settings = settings or get_settings()

    def initialize(self) -> Dict[str, str]:
        directories = {
            "raw": self.settings.raw_data_dir,
            "processed": self.settings.processed_data_dir,
            "features": self.settings.feature_store_dir,
            "vectors": self.settings.vector_store_dir,
            "models": self.settings.model_dir,
            "reports": self.settings.reports_dir,
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        manifest = {
            "created_at": datetime.utcnow().isoformat(),
            "environment": self.settings.environment,
            "database_url": self.settings.database_url,
            "directories": {name: str(path) for name, path in directories.items()},
            "phase1_storage_strategy": {
                "raw": "Original API/file downloads, unchanged.",
                "processed": "Cleaned tables ready for analysis.",
                "features": "ML-ready feature tables.",
                "vectors": "RAG indexes and embedding metadata.",
                "models": "TensorFlow/PyTorch/scikit-learn artifacts.",
                "reports": "Markdown, CSV, JSON, and dashboard outputs.",
            },
        }
        self.save_json("processed", "storage_manifest.json", manifest)
        return {name: str(path) for name, path in directories.items()}

    def save_dataframe(self, layer: str, filename: str, dataframe: pd.DataFrame) -> Path:
        path = self._layer_dir(layer) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".parquet":
            dataframe.to_parquet(path, index=False)
        else:
            dataframe.to_csv(path, index=False)
        return path

    def load_dataframe(self, layer: str, filename: str) -> pd.DataFrame:
        path = self._layer_dir(layer) / filename
        if path.suffix.lower() == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)

    def save_json(self, layer: str, filename: str, payload: Dict[str, Any]) -> Path:
        path = self._layer_dir(layer) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def _layer_dir(self, layer: str) -> Path:
        mapping = {
            "raw": self.settings.raw_data_dir,
            "processed": self.settings.processed_data_dir,
            "features": self.settings.feature_store_dir,
            "vectors": self.settings.vector_store_dir,
            "models": self.settings.model_dir,
            "reports": self.settings.reports_dir,
        }
        if layer not in mapping:
            raise ValueError(f"Unknown storage layer: {layer}")
        return mapping[layer]

