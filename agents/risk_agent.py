"""
Risk Agent.

Phase 1 calculates transparent risk features. The TensorFlow model can later be
trained on the same feature contract and used inside this agent.
"""

from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd

from config import get_settings
from ml_models.risk_scorer import RiskScorer

from .schemas import AgentResult


class RiskAgent:
    """Produces a financial risk score for each ticker."""

    def __init__(self):
        self.settings = get_settings()
        self.feature_path = self.settings.feature_store_dir / "phase1_model_features.csv"
        self.model_path = self.settings.model_dir / "phase1_risk_model.pkl"
        self._feature_cache = None
        self._model = None

    def run(self, tickers: Iterable[str], sentiment_data: Dict[str, dict]) -> AgentResult:
        results = {}
        model_loaded = self._load_model()
        feature_frame = self._load_features() if model_loaded else pd.DataFrame()

        for ticker in tickers:
            model_result = self._predict_with_model(ticker, feature_frame) if model_loaded else None
            results[ticker] = model_result or self._fallback_risk(ticker, sentiment_data)

        portfolio_risk = float(np.mean([item["risk_score"] for item in results.values()]))
        source = "trained_phase1_model" if model_loaded else "transparent_proxy"
        return AgentResult(
            agent_name="Risk Agent",
            status="success",
            summary=f"Computed risk profile for {len(results)} companies.",
            data={"tickers": results, "portfolio_risk": round(portfolio_risk, 2), "source": source},
            confidence=0.78 if model_loaded else 0.68,
            warnings=[] if model_loaded else ["Phase 1 risk uses transparent proxies until baseline models are trained."],
        )

    def _load_model(self) -> bool:
        if self._model is not None:
            return True
        if not self.model_path.exists():
            return False
        try:
            self._model = RiskScorer.load(self.model_path)
            return True
        except Exception:
            self._model = None
            return False

    def _load_features(self) -> pd.DataFrame:
        if self._feature_cache is not None:
            return self._feature_cache
        if not self.feature_path.exists():
            self._feature_cache = pd.DataFrame()
        else:
            self._feature_cache = pd.read_csv(self.feature_path)
            self._feature_cache["ticker"] = self._feature_cache["ticker"].astype(str).str.upper()
        return self._feature_cache

    def _predict_with_model(self, ticker: str, feature_frame: pd.DataFrame) -> Dict | None:
        if feature_frame.empty or self._model is None:
            return None
        row = feature_frame[feature_frame["ticker"] == ticker.upper()]
        if row.empty:
            return None

        labels, probabilities = self._model.predict_proba(row.head(1))
        prediction = self._model.predict(row.head(1))[0]
        probability_map = dict(zip(labels, probabilities[0]))
        confidence = float(max(probability_map.values()))
        risk_score = {"Low": 25.0, "Medium": 50.0, "High": 75.0}.get(prediction, 50.0)
        row_data = row.iloc[0]
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": prediction,
            "model_confidence": round(confidence, 3),
            "volatility_proxy": round(float(row_data.get("volatility_20", 0)), 2),
            "leverage_proxy": round(float(row_data.get("leverage_proxy", 0)), 2),
            "sentiment_risk": round(float((1 - row_data.get("sentiment_score", 0.5)) * 100), 2),
            "model_probabilities": {label: round(float(value), 3) for label, value in probability_map.items()},
        }

    def _fallback_risk(self, ticker: str, sentiment_data: Dict[str, dict]) -> Dict:
        seed = self._stable_seed(ticker)
        volatility = 12 + (seed % 28)
        leverage_proxy = 20 + ((seed * 7) % 55)
        sentiment_score = sentiment_data.get(ticker, {}).get("sentiment_score", 0.5)
        sentiment_risk = (1 - sentiment_score) * 100

        risk_score = np.average(
            [volatility, leverage_proxy, sentiment_risk],
            weights=[0.45, 0.30, 0.25],
        )

        return {
            "risk_score": round(float(risk_score), 2),
            "risk_level": self._risk_level(risk_score),
            "volatility_proxy": round(float(volatility), 2),
            "leverage_proxy": round(float(leverage_proxy), 2),
            "sentiment_risk": round(float(sentiment_risk), 2),
        }

    def _stable_seed(self, ticker: str) -> int:
        return sum(ord(char) for char in ticker.upper())

    def _risk_level(self, score: float) -> str:
        if score < 35:
            return "Low"
        if score < 60:
            return "Medium"
        return "High"
