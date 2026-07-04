"""
Phase 1 large-universe data pipeline.

This module turns the cached US equity universe into an ML-ready feature table.
It is local-first and deterministic so the project can demo at scale without
depending on network calls. Live OHLCV/fundamental enrichment can be layered on
top of the same feature contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable

import numpy as np
import pandas as pd

from data_layer.company_universe import USEquityUniverseBuilder
from storage import DataStore


class Phase1DataPipeline:
    """Builds Phase 1 universe, feature, label, and summary artifacts."""

    FEATURE_FILE = "phase1_model_features.csv"
    SUMMARY_FILE = "phase1_data_pipeline_summary.json"

    def __init__(self, store: DataStore | None = None):
        self.store = store or DataStore()

    def build(
        self,
        min_universe_count: int = 10000,
        fetch_remote_universe: bool = False,
    ) -> pd.DataFrame:
        self.store.initialize()
        universe = USEquityUniverseBuilder(self.store).build(
            fetch_remote=fetch_remote_universe,
            min_count=min_universe_count,
        )
        features = self._build_feature_table(universe)

        self.store.save_dataframe("features", self.FEATURE_FILE, features)
        self.store.save_json(
            "processed",
            self.SUMMARY_FILE,
            {
                "generated_at": datetime.utcnow().isoformat(),
                "universe_rows": int(len(universe)),
                "feature_rows": int(len(features)),
                "feature_columns": list(features.columns),
                "risk_label_distribution": features["risk_label"].value_counts().to_dict(),
                "forecast_label_distribution": features["forecast_label"].value_counts().to_dict(),
                "data_contract": {
                    "ticker": "US equity ticker from Nasdaq/SEC universe.",
                    "market_features": "Deterministic baseline market/fundamental proxies for scalable Phase 1 training.",
                    "risk_label": "Low/Medium/High label generated from volatility, drawdown, leverage, and sentiment risk.",
                    "forecast_label": "Down/Flat/Up label generated from deterministic forward-return proxy.",
                },
                "next_enrichment": [
                    "Replace proxy market features with cached OHLCV/fundamentals where available.",
                    "Add real news sentiment and filing-derived features.",
                    "Persist live-fetch failures and data freshness by ticker.",
                ],
            },
        )
        return features

    def _build_feature_table(self, universe: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in universe.to_dict(orient="records"):
            ticker = str(row.get("ticker", "")).upper().strip()
            if not ticker:
                continue

            seed = self._stable_seed(ticker)
            rng = np.random.default_rng(seed)
            company_name = str(row.get("company_name", ticker))
            exchange = str(row.get("exchange", "N/A"))
            source = str(row.get("source", "N/A"))

            base_price = 8 + (seed % 490) + rng.normal(0, 3)
            daily_return_20d = rng.normal(((seed % 17) - 8) / 120, 0.035)
            momentum_30d = rng.normal(((seed % 23) - 11) / 30, 0.18)
            volatility_20 = 8 + (seed % 45) + abs(rng.normal(0, 5))
            volatility_60 = volatility_20 * rng.uniform(0.85, 1.25)
            max_drawdown = -1 * (5 + (seed % 55) + abs(rng.normal(0, 6)))
            volume_ratio = max(0.15, rng.normal(1.0 + ((seed % 7) - 3) / 10, 0.25))
            rsi_14 = float(np.clip(50 + momentum_30d * 42 + rng.normal(0, 9), 5, 95))
            leverage_proxy = 10 + ((seed * 11) % 85)
            market_cap_proxy = int((seed % 800 + 5) * 1_000_000 * rng.uniform(8, 160))
            sentiment_score = float(np.clip(0.5 + rng.normal(0, 0.18) + momentum_30d * 0.08, 0.03, 0.97))
            liquidity_score = float(np.clip(100 - abs(volume_ratio - 1) * 35 + rng.normal(0, 6), 5, 100))

            future_return_30d = (
                momentum_30d * 0.42
                + daily_return_20d * 3.5
                + (sentiment_score - 0.5) * 0.18
                - volatility_20 / 850
                + rng.normal(0, 0.055)
            )
            risk_score = (
                volatility_20 * 0.35
                + abs(max_drawdown) * 0.25
                + leverage_proxy * 0.20
                + (1 - sentiment_score) * 100 * 0.15
                + (100 - liquidity_score) * 0.05
            )

            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "exchange": exchange,
                    "source": source,
                    "price_current": round(float(base_price), 2),
                    "daily_return_20d": round(float(daily_return_20d), 5),
                    "momentum_30d": round(float(momentum_30d), 5),
                    "volatility_20": round(float(volatility_20), 4),
                    "volatility_60": round(float(volatility_60), 4),
                    "max_drawdown": round(float(max_drawdown), 4),
                    "volume_ratio": round(float(volume_ratio), 4),
                    "rsi_14": round(float(rsi_14), 4),
                    "leverage_proxy": round(float(leverage_proxy), 4),
                    "market_cap_proxy": market_cap_proxy,
                    "sentiment_score": round(float(sentiment_score), 5),
                    "liquidity_score": round(float(liquidity_score), 4),
                    "future_return_30d": round(float(future_return_30d), 5),
                    "risk_score_label_basis": round(float(risk_score), 4),
                }
            )

        features = pd.DataFrame(rows)
        if features.empty:
            return features

        low_cut = features["risk_score_label_basis"].quantile(0.33)
        high_cut = features["risk_score_label_basis"].quantile(0.66)
        features["risk_label"] = np.select(
            [
                features["risk_score_label_basis"] <= low_cut,
                features["risk_score_label_basis"] >= high_cut,
            ],
            ["Low", "High"],
            default="Medium",
        )
        features["forecast_label"] = np.select(
            [
                features["future_return_30d"] <= -0.025,
                features["future_return_30d"] >= 0.025,
            ],
            ["Down", "Up"],
            default="Flat",
        )
        return features

    def _stable_seed(self, ticker: str) -> int:
        return sum((idx + 1) * ord(char) for idx, char in enumerate(ticker.upper()))


def build_phase1_data(min_universe_count: int = 10000, fetch_remote_universe: bool = False) -> pd.DataFrame:
    return Phase1DataPipeline().build(
        min_universe_count=min_universe_count,
        fetch_remote_universe=fetch_remote_universe,
    )


if __name__ == "__main__":
    frame = build_phase1_data()
    print(f"Phase 1 feature table generated: {len(frame)} rows x {len(frame.columns)} columns")
