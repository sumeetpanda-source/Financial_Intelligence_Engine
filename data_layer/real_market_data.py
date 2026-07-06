"""Real market-data ingestion and point-in-time feature engineering."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf

from data_layer.yfinance_support import configure_yfinance_cache
from storage import DataStore


DEFAULT_REAL_DATA_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "JPM",
    "BAC",
    "GS",
    "XOM",
    "CVX",
    "JNJ",
    "UNH",
    "PFE",
    "WMT",
    "COST",
    "HD",
    "KO",
    "PEP",
]


class RealMarketDataPipeline:
    """Fetches cached real observations and builds leakage-aware ML features."""

    HISTORY_FILE = "real_market_history.csv"
    FUNDAMENTALS_FILE = "real_company_fundamentals.csv"
    TRAINING_FEATURE_FILE = "real_market_training_features.csv"
    LATEST_FEATURE_FILE = "real_market_latest_features.csv"
    SUMMARY_FILE = "real_market_data_summary.json"

    def __init__(self, store: DataStore | None = None):
        self.store = store or DataStore()
        self.settings = self.store.settings
        self.raw_market_dir = self.settings.raw_data_dir / "market"
        configure_yfinance_cache()

    def run(
        self,
        tickers: Iterable[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        years: int = 5,
        refresh: bool = False,
        include_fundamentals: bool = True,
    ) -> dict:
        self.store.initialize()
        self.raw_market_dir.mkdir(parents=True, exist_ok=True)
        selected = self._normalize_tickers(tickers or DEFAULT_REAL_DATA_TICKERS)
        end_date = end or date.today().isoformat()
        start_date = start or (date.today() - timedelta(days=365 * years + 30)).isoformat()

        history_frames: list[pd.DataFrame] = []
        fundamental_rows: list[dict] = []
        failures: list[dict] = []

        for ticker in selected:
            try:
                history = self._load_or_fetch_history(
                    ticker=ticker,
                    start=start_date,
                    end=end_date,
                    refresh=refresh,
                )
                if len(history) < 100:
                    raise ValueError(f"only {len(history)} daily observations returned")
                history_frames.append(history)
            except Exception as exc:
                failures.append({"ticker": ticker, "stage": "history", "error": str(exc)})
                continue

            if include_fundamentals:
                try:
                    fundamental_rows.append(
                        self._load_or_fetch_fundamentals(ticker=ticker, refresh=refresh)
                    )
                except Exception as exc:
                    failures.append({"ticker": ticker, "stage": "fundamentals", "error": str(exc)})

        if not history_frames:
            raise RuntimeError(
                "No real market history was available. Check network access or cached files in "
                f"{self.raw_market_dir}. Failures: {json.dumps(failures)}"
            )

        history = pd.concat(history_frames, ignore_index=True)
        fundamentals = pd.DataFrame(fundamental_rows)
        training_features, latest_features = self.build_features(history, fundamentals)
        if training_features.empty:
            raise RuntimeError("Real history was fetched, but it did not produce enough training rows.")

        self.store.save_dataframe("processed", self.HISTORY_FILE, history)
        self.store.save_dataframe("processed", self.FUNDAMENTALS_FILE, fundamentals)
        self.store.save_dataframe("features", self.TRAINING_FEATURE_FILE, training_features)
        self.store.save_dataframe("features", self.LATEST_FEATURE_FILE, latest_features)

        summary = {
            "data_source": "Yahoo Finance via yfinance",
            "requested_tickers": selected,
            "successful_tickers": sorted(history["ticker"].unique().tolist()),
            "ticker_count": int(history["ticker"].nunique()),
            "history_rows": int(len(history)),
            "training_rows": int(len(training_features)),
            "latest_feature_rows": int(len(latest_features)),
            "date_start": str(history["date"].min()),
            "date_end": str(history["date"].max()),
            "fundamental_rows": int(len(fundamentals)),
            "failures": failures,
            "label_contract": {
                "forecast_label": "Observed 20-trading-day forward adjusted return.",
                "risk_label": "Observed 20-trading-day forward annualized volatility.",
            },
        }
        self.store.save_json("processed", self.SUMMARY_FILE, summary)
        return summary

    def build_features(
        self,
        history: pd.DataFrame,
        fundamentals: pd.DataFrame | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Build training rows and latest inference rows from real observations."""
        fundamentals = fundamentals if fundamentals is not None else pd.DataFrame()
        fundamental_map = {}
        if not fundamentals.empty and "ticker" in fundamentals:
            fundamental_map = {
                str(row["ticker"]).upper(): row
                for row in fundamentals.to_dict(orient="records")
            }

        training_frames: list[pd.DataFrame] = []
        latest_rows: list[pd.DataFrame] = []
        for ticker, group in history.groupby("ticker"):
            frame = group.copy()
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
            frame = frame.dropna(subset=["date"]).sort_values("date").drop_duplicates("date")
            price = frame["adj_close"].fillna(frame["close"]).astype(float)
            returns = price.pct_change()
            volume = frame["volume"].astype(float).replace(0, np.nan)
            fundamental = fundamental_map.get(str(ticker).upper(), {})

            feature_frame = pd.DataFrame(
                {
                    "ticker": str(ticker).upper(),
                    "feature_date": frame["date"],
                    "price_current": price,
                    "daily_return_20d": price.pct_change(20),
                    "momentum_30d": price.pct_change(30),
                    "volatility_20": returns.rolling(20).std() * np.sqrt(252) * 100,
                    "volatility_60": returns.rolling(60).std() * np.sqrt(252) * 100,
                    "max_drawdown": (price / price.rolling(60).max() - 1) * 100,
                    "volume_ratio": volume / volume.rolling(20).mean(),
                    "rsi_14": self._rsi(price, 14),
                    "leverage_proxy": self._number(fundamental.get("debt_to_equity"), 50.0),
                    "market_cap_proxy": self._number(fundamental.get("market_cap"), 0.0),
                    "sentiment_score": 0.5,
                    "liquidity_score": self._liquidity_score(price * volume),
                    "future_return_30d": price.shift(-20) / price - 1,
                    "future_realized_volatility_20": (
                        returns.rolling(20).std().shift(-20) * np.sqrt(252) * 100
                    ),
                    "data_source": "yfinance_real",
                }
            )
            feature_frame["risk_score_label_basis"] = feature_frame[
                "future_realized_volatility_20"
            ]
            feature_frame["risk_label"] = np.select(
                [
                    feature_frame["future_realized_volatility_20"] < 20,
                    feature_frame["future_realized_volatility_20"] >= 40,
                ],
                ["Low", "High"],
                default="Medium",
            )
            feature_frame["forecast_label"] = np.select(
                [
                    feature_frame["future_return_30d"] <= -0.025,
                    feature_frame["future_return_30d"] >= 0.025,
                ],
                ["Down", "Up"],
                default="Flat",
            )

            required_features = [
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
            inference_rows = feature_frame.dropna(subset=required_features)
            if not inference_rows.empty:
                latest_rows.append(inference_rows.tail(1).copy())

            training_rows = feature_frame.dropna(
                subset=required_features
                + ["future_return_30d", "future_realized_volatility_20"]
            )
            if not training_rows.empty:
                training_frames.append(training_rows)

        training = pd.concat(training_frames, ignore_index=True) if training_frames else pd.DataFrame()
        latest = pd.concat(latest_rows, ignore_index=True) if latest_rows else pd.DataFrame()
        for frame in (training, latest):
            if not frame.empty:
                frame["feature_date"] = pd.to_datetime(frame["feature_date"]).dt.strftime("%Y-%m-%d")
        return training, latest

    def _load_or_fetch_history(
        self,
        ticker: str,
        start: str,
        end: str,
        refresh: bool,
    ) -> pd.DataFrame:
        cache_path = self.raw_market_dir / f"{ticker}_daily.csv"
        if cache_path.exists() and not refresh:
            cached = pd.read_csv(cache_path)
            if len(cached) >= 100:
                return cached

        ticker_client = yf.Ticker(ticker)
        try:
            frame = ticker_client.history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                actions=False,
                repair=True,
            )
        except Exception:
            frame = ticker_client.history(
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                actions=False,
            )
        normalized = self._normalize_history(ticker, frame)
        normalized.to_csv(cache_path, index=False)
        return normalized

    def _load_or_fetch_fundamentals(self, ticker: str, refresh: bool) -> dict:
        cache_path = self.raw_market_dir / f"{ticker}_fundamentals.json"
        if cache_path.exists() and not refresh:
            return json.loads(cache_path.read_text(encoding="utf-8"))

        client = yf.Ticker(ticker)
        info = client.get_info() if hasattr(client, "get_info") else client.info
        row = {
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
            "market_cap": self._json_number(info.get("marketCap")),
            "debt_to_equity": self._json_number(info.get("debtToEquity")),
            "trailing_pe": self._json_number(info.get("trailingPE")),
            "price_to_book": self._json_number(info.get("priceToBook")),
            "return_on_equity": self._json_number(info.get("returnOnEquity")),
            "profit_margins": self._json_number(info.get("profitMargins")),
            "total_revenue": self._json_number(info.get("totalRevenue")),
            "data_source": "yfinance_real",
        }
        cache_path.write_text(json.dumps(row, indent=2), encoding="utf-8")
        return row

    @staticmethod
    def _normalize_history(ticker: str, frame: pd.DataFrame) -> pd.DataFrame:
        if frame is None or frame.empty:
            return pd.DataFrame()
        normalized = frame.reset_index()
        date_column = "Date" if "Date" in normalized else "Datetime"
        column_map = {
            date_column: "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
        normalized = normalized.rename(columns=column_map)
        if "adj_close" not in normalized:
            normalized["adj_close"] = normalized["close"]
        normalized["ticker"] = ticker
        normalized["date"] = pd.to_datetime(normalized["date"], utc=True).dt.date.astype(str)
        columns = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]
        for column in columns:
            if column not in normalized:
                normalized[column] = np.nan
        return normalized[columns].dropna(subset=["date", "close"]).reset_index(drop=True)

    @staticmethod
    def _rsi(price: pd.Series, window: int) -> pd.Series:
        change = price.diff()
        gain = change.clip(lower=0).rolling(window).mean()
        loss = -change.clip(upper=0).rolling(window).mean()
        relative_strength = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + relative_strength))
        return rsi.fillna(50.0)

    @staticmethod
    def _liquidity_score(dollar_volume: pd.Series) -> pd.Series:
        log_volume = np.log10(dollar_volume.clip(lower=1))
        return ((log_volume - 4) * 15).clip(lower=5, upper=100)

    @staticmethod
    def _normalize_tickers(tickers: Iterable[str]) -> list[str]:
        normalized = [str(ticker).upper().strip() for ticker in tickers if str(ticker).strip()]
        return list(dict.fromkeys(normalized))

    @staticmethod
    def _number(value, default: float) -> float:
        try:
            numeric = float(value)
            return numeric if np.isfinite(numeric) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _json_number(value):
        try:
            numeric = float(value)
            return numeric if np.isfinite(numeric) else None
        except (TypeError, ValueError):
            return None
