"""
Sentiment Agent.

Phase 1 uses a transparent financial keyword model and generated/demo news.
Phase 2 can replace this with FinBERT fine-tuning while preserving the output.
"""

from typing import Dict, Iterable, List

import numpy as np

from data_layer.sentiment_analyzer import FinancialSentimentAnalyzer

from .schemas import AgentResult, EvidenceItem


class SentimentAgent:
    """Scores financial sentiment for requested tickers and retrieved text."""

    def __init__(self):
        self.analyzer = FinancialSentimentAnalyzer()

    def run(self, tickers: Iterable[str], retrieved_evidence: List[EvidenceItem]) -> AgentResult:
        tickers = list(tickers)
        np.random.seed(sum(sum(ord(char) for char in ticker) for ticker in tickers))
        news_articles = self.analyzer.generate_sample_news_dataset(tickers, days=14)
        result_by_ticker: Dict[str, dict] = {}

        retrieved_text = " ".join(item.text for item in retrieved_evidence)
        retrieved_sentiment = self.analyzer.analyze_sentiment_from_text(retrieved_text) if retrieved_text else None

        for ticker in tickers:
            indicators = self.analyzer.get_sentiment_indicators(news_articles, ticker) or {}
            score = float(indicators.get("avg_sentiment_score", 0.5))

            if retrieved_sentiment:
                score = float(np.mean([score, retrieved_sentiment["sentiment_score"]]))

            result_by_ticker[ticker] = {
                "sentiment_score": round(score, 3),
                "sentiment_label": self._label(score),
                "news_count": indicators.get("total_news_articles", 0),
                "trend": indicators.get("sentiment_trend", "Unknown"),
            }

        average_score = float(np.mean([item["sentiment_score"] for item in result_by_ticker.values()]))
        return AgentResult(
            agent_name="Sentiment Agent",
            status="success",
            summary=f"Calculated sentiment for {len(result_by_ticker)} companies.",
            data={"tickers": result_by_ticker, "portfolio_sentiment": round(average_score, 3)},
            confidence=0.72,
            warnings=["Phase 1 sentiment is explainable/demo-grade; FinBERT should be enabled for production."],
        )

    def _label(self, score: float) -> str:
        if score >= 0.62:
            return "Positive"
        if score <= 0.38:
            return "Negative"
        return "Neutral"
