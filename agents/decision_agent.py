"""
Decision Agent.

Combines retrieval, sentiment, risk, and forecast outputs into an investment
decision. This is the baseline market-standard scoring layer for Phase 1.
"""

from typing import Dict, Iterable

import numpy as np

from .schemas import AgentResult


class DecisionAgent:
    """Creates Buy/Hold/Sell recommendations from agent outputs."""

    def run(
        self,
        tickers: Iterable[str],
        sentiment_data: Dict[str, dict],
        risk_data: Dict[str, dict],
        forecast_data: Dict[str, dict],
    ) -> AgentResult:
        decisions = {}
        for ticker in tickers:
            sentiment_score = sentiment_data.get(ticker, {}).get("sentiment_score", 0.5)
            risk_score = risk_data.get(ticker, {}).get("risk_score", 50)
            expected_return = forecast_data.get(ticker, {}).get("expected_return_pct", 0)

            return_component = min(max((expected_return + 10) / 20 * 100, 0), 100)
            score = (
                sentiment_score * 100 * 0.30
                + (100 - risk_score) * 0.35
                + return_component * 0.35
            )

            decisions[ticker] = {
                "investment_score": round(float(score), 2),
                "recommendation": self._recommendation(score),
                "confidence": round(float(min(max(score / 100, 0.35), 0.92)), 2),
                "drivers": {
                    "sentiment_score": round(float(sentiment_score), 3),
                    "risk_score": round(float(risk_score), 2),
                    "expected_return_pct": round(float(expected_return), 2),
                },
            }

        average_score = float(np.mean([item["investment_score"] for item in decisions.values()]))
        return AgentResult(
            agent_name="Decision Agent",
            status="success",
            summary="Generated investment decisions from multi-agent outputs.",
            data={"tickers": decisions, "average_investment_score": round(average_score, 2)},
            confidence=0.70,
        )

    def _recommendation(self, score: float) -> str:
        if score >= 75:
            return "Strong Buy"
        if score >= 62:
            return "Buy"
        if score >= 45:
            return "Hold"
        if score >= 32:
            return "Sell"
        return "Strong Sell"

