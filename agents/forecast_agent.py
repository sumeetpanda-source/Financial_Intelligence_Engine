"""
Forecast Agent.

Phase 1 creates a reproducible short-horizon forecast signal. Phase 2 can replace
this with a PyTorch LSTM/Temporal model trained on historical OHLCV data.
"""

from copy import deepcopy
from typing import Iterable

import numpy as np
import pandas as pd

from config import get_settings
from ml_models.price_predictor import PricePredictor

from .schemas import AgentResult


class ForecastAgent:
    """Generates short-horizon return forecasts."""

    def __init__(self):
        self.settings = get_settings()
        self.real_feature_path = (
            self.settings.feature_store_dir / "real_market_latest_features.csv"
        )
        self.proxy_feature_path = self.settings.feature_store_dir / "phase1_model_features.csv"
        self.model_path = self.settings.model_dir / "phase1_forecast_model.pkl"
        self._feature_cache = None
        self._feature_rows: dict[str, pd.DataFrame] = {}
        self._model = None
        self._prediction_cache: dict[tuple[str, int], dict] = {}

    def run(self, tickers: Iterable[str], horizon_days: int = 30) -> AgentResult:
        results = {}
        model_loaded = self._load_model()
        feature_frame = self._load_features() if model_loaded else pd.DataFrame()
        model_results = (
            self._predict_many_with_model(tickers, feature_frame, horizon_days)
            if model_loaded
            else {}
        )

        for ticker in tickers:
            model_result = model_results.get(ticker.upper()) if model_loaded else None
            results[ticker] = model_result or self._fallback_forecast(ticker, horizon_days)

        avg_return = float(np.mean([item["expected_return_pct"] for item in results.values()]))
        real_features = not feature_frame.empty and "data_source" in feature_frame and (
            feature_frame["data_source"].astype(str) == "yfinance_real"
        ).any()
        source = (
            "real_market_trained_model"
            if model_loaded and real_features
            else "trained_phase1_model"
            if model_loaded
            else "baseline_signal"
        )
        model_confidences = [
            float(item.get("model_confidence", 0.0))
            for item in results.values()
            if "model_confidence" in item
        ]
        confidence = (
            float(np.mean(model_confidences))
            if model_confidences
            else 0.62
        )
        return AgentResult(
            agent_name="Forecast Agent",
            status="success",
            summary=f"Generated {horizon_days}-day forecast signals.",
            data={"tickers": results, "average_expected_return_pct": round(avg_return, 2), "source": source},
            confidence=round(confidence, 3),
            warnings=[] if model_loaded else ["Phase 1 forecast is a baseline signal; train baseline models for model-backed output."],
        )

    def _load_model(self) -> bool:
        if self._model is not None:
            return True
        if not self.model_path.exists():
            return False
        try:
            self._model = PricePredictor.load(self.model_path)
            return True
        except Exception:
            self._model = None
            return False

    def _load_features(self) -> pd.DataFrame:
        if self._feature_cache is not None:
            return self._feature_cache
        feature_path = (
            self.real_feature_path
            if self.real_feature_path.exists()
            else self.proxy_feature_path
        )
        if not feature_path.exists():
            self._feature_cache = pd.DataFrame()
        else:
            self._feature_cache = pd.read_csv(feature_path)
            self._feature_cache["ticker"] = self._feature_cache["ticker"].astype(str).str.upper()
        return self._feature_cache

    def _predict_with_model(self, ticker: str, feature_frame: pd.DataFrame, horizon_days: int) -> dict | None:
        return self._predict_many_with_model([ticker], feature_frame, horizon_days).get(ticker.upper())

    def _predict_many_with_model(
        self,
        tickers: Iterable[str],
        feature_frame: pd.DataFrame,
        horizon_days: int,
    ) -> dict[str, dict]:
        if feature_frame.empty or self._model is None:
            return {}

        results: dict[str, dict] = {}
        uncached_tickers = []
        uncached_rows = []
        for ticker in dict.fromkeys(ticker.upper() for ticker in tickers):
            cache_key = (ticker, int(horizon_days))
            if cache_key in self._prediction_cache:
                results[ticker] = deepcopy(self._prediction_cache[cache_key])
                continue
            row = self._feature_row(ticker, feature_frame)
            if row.empty:
                continue
            uncached_tickers.append(ticker)
            uncached_rows.append(row)

        if uncached_rows:
            batch = pd.concat(uncached_rows, ignore_index=True)
            labels, probabilities = self._model.predict_proba(batch)
            predictions = self._model.predict(batch)
            for index, ticker in enumerate(uncached_tickers):
                probability_map = dict(zip(labels, probabilities[index]))
                confidence = float(max(probability_map.values()))
                expected_return = float(
                    sum(
                        probability * self._model.class_return_means.get(label, 0.0)
                        for label, probability in zip(labels, probabilities[index])
                    )
                    * 100
                )
                annualized_volatility_pct = float(batch.iloc[index].get("volatility_20", 0))
                forecast_volatility_pct = annualized_volatility_pct * np.sqrt(horizon_days / 252)
                result = {
                    "horizon_days": horizon_days,
                    "expected_return_pct": round(expected_return, 2),
                    "forecast_direction": predictions[index],
                    "forecast_volatility_pct": round(forecast_volatility_pct, 2),
                    "model_confidence": round(confidence, 3),
                    "model_probabilities": {label: round(float(value), 3) for label, value in probability_map.items()},
                }
                cache_key = (ticker, int(horizon_days))
                self._prediction_cache[cache_key] = result
                results[ticker] = deepcopy(result)
        return results

    def _feature_row(self, ticker: str, feature_frame: pd.DataFrame) -> pd.DataFrame:
        if ticker not in self._feature_rows:
            self._feature_rows[ticker] = feature_frame[feature_frame["ticker"] == ticker].head(1)
        return self._feature_rows[ticker]

    def _fallback_forecast(self, ticker: str, horizon_days: int) -> dict:
        prices = self._synthetic_price_series(ticker)
        returns = prices.pct_change().dropna()
        recent_momentum = returns.tail(20).mean() * horizon_days
        volatility = returns.tail(60).std() * np.sqrt(horizon_days)
        expected_return = float(recent_momentum * 100)

        return {
            "horizon_days": horizon_days,
            "expected_return_pct": round(expected_return, 2),
            "forecast_direction": "Up" if expected_return > 1 else "Down" if expected_return < -1 else "Flat",
            "forecast_volatility_pct": round(float(volatility * 100), 2),
        }

    def _synthetic_price_series(self, ticker: str) -> pd.Series:
        seed = sum(ord(char) for char in ticker.upper())
        rng = np.random.default_rng(seed)
        dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=180)
        drift = ((seed % 9) - 4) / 1000
        shocks = rng.normal(loc=drift, scale=0.018, size=len(dates))
        prices = 100 * np.cumprod(1 + shocks)
        return pd.Series(prices, index=dates, name=ticker)
