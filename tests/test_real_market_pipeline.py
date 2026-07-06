"""Tests for real-market feature engineering and chronological training."""

import numpy as np
import pandas as pd

from data_layer.real_market_data import RealMarketDataPipeline
from ml_models.price_predictor import PricePredictor
from ml_models.real_market_trainer import RealMarketModelTrainer


def synthetic_history(tickers=("AAPL", "MSFT"), periods=260):
    rows = []
    dates = pd.bdate_range("2024-01-02", periods=periods)
    for ticker_index, ticker in enumerate(tickers):
        trend = np.linspace(100 + ticker_index * 20, 145 + ticker_index * 25, periods)
        wave = np.sin(np.arange(periods) / 7) * (2 + ticker_index)
        prices = trend + wave
        for index, current_date in enumerate(dates):
            close = float(prices[index])
            rows.append(
                {
                    "ticker": ticker,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "open": close * 0.995,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "adj_close": close,
                    "volume": 1_000_000 + index * 1000,
                }
            )
    return pd.DataFrame(rows)


def test_real_market_features_use_observed_forward_outcomes():
    fundamentals = pd.DataFrame(
        [
            {"ticker": "AAPL", "debt_to_equity": 75.0, "market_cap": 3_000_000_000_000},
            {"ticker": "MSFT", "debt_to_equity": 50.0, "market_cap": 2_800_000_000_000},
        ]
    )
    training, latest = RealMarketDataPipeline().build_features(
        synthetic_history(),
        fundamentals,
    )

    assert not training.empty
    assert training["ticker"].nunique() == 2
    assert training["future_return_30d"].notna().all()
    assert training["future_realized_volatility_20"].notna().all()
    assert set(training["data_source"]) == {"yfinance_real"}
    assert len(latest) == 2
    assert latest["feature_date"].max() > training["feature_date"].max()


def test_real_market_training_split_is_chronological():
    features, _ = RealMarketDataPipeline().build_features(synthetic_history())
    train, test, split = RealMarketModelTrainer._time_split(features)

    assert pd.to_datetime(train["feature_date"]).max() < pd.to_datetime(test["feature_date"]).min()
    assert split["train_end_date"] < split["test_start_date"]


def test_forecast_expected_return_uses_model_probabilities_not_future_column():
    features, latest = RealMarketDataPipeline().build_features(synthetic_history())
    model = PricePredictor().train(features)
    inference = latest.copy()
    inference["future_return_30d"] = 999.0

    expected = model.expected_return(inference)

    assert len(expected) == len(inference)
    assert all(abs(value) < 1 for value in expected)
