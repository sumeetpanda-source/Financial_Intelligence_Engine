"""
Orchestrator Agent for the Phase 1 application.
"""

import re
import csv
import time
from pathlib import Path
from typing import Iterable, List, Optional

from config import get_settings
from genai_layer import build_genai_provider

from .decision_agent import DecisionAgent
from .explainability_agent import ExplainabilityAgent
from .forecast_agent import ForecastAgent
from .query_intelligence import QueryIntelligence, QueryProfile
from .retriever_agent import RetrieverAgent
from .risk_agent import RiskAgent
from .sentiment_agent import SentimentAgent


class OrchestratorAgent:
    """Coordinates Phase 1 agents from user query to final report."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parents[1]
        self.settings = get_settings(self.project_root)
        self.retriever = RetrieverAgent()
        self.sentiment = SentimentAgent()
        self.risk = RiskAgent()
        self.forecast = ForecastAgent()
        self.decision = DecisionAgent()
        self.explainability = ExplainabilityAgent(build_genai_provider(self.settings))
        self.query_intelligence = QueryIntelligence()

    def run(
        self,
        query: str,
        tickers: Optional[Iterable[str]] = None,
        document_paths: Optional[Iterable[str]] = None,
    ) -> dict:
        total_start = time.perf_counter()
        timings: dict[str, float] = {}

        def timed(step_name: str, callback):
            start = time.perf_counter()
            output = callback()
            timings[step_name] = round(time.perf_counter() - start, 3)
            return output

        query_profile = timed("query_intelligence", lambda: self.query_intelligence.classify(query))
        selected_tickers = timed(
            "ticker_selection",
            lambda: list(
                tickers
                or self._extract_tickers(query)
                or self._default_tickers(query, query_profile)
            ),
        )
        selected_documents = list(document_paths or self._default_document_paths())

        retrieval_top_k = 3 if query_profile.needs_allocation else 5
        retrieval = timed(
            "retriever",
            lambda: self.retriever.run(
                query=query,
                document_paths=selected_documents,
                top_k=retrieval_top_k,
            ),
        )
        sentiment = timed("sentiment", lambda: self.sentiment.run(selected_tickers, retrieval.evidence))
        risk = timed("risk", lambda: self.risk.run(selected_tickers, sentiment.data["tickers"]))
        forecast = timed(
            "forecast",
            lambda: self.forecast.run(selected_tickers, horizon_days=query_profile.horizon_days),
        )
        decision = timed(
            "decision",
            lambda: self.decision.run(
                tickers=selected_tickers,
                sentiment_data=sentiment.data["tickers"],
                risk_data=risk.data["tickers"],
                forecast_data=forecast.data["tickers"],
            ),
        )
        explanation = timed(
            "explainability",
            lambda: self.explainability.run(
                query=query,
                tickers=selected_tickers,
                retrieved_evidence=retrieval.evidence,
                sentiment_data=sentiment.data["tickers"],
                risk_data=risk.data["tickers"],
                forecast_data=forecast.data["tickers"],
                decision_data=decision.data["tickers"],
            ),
        )
        total_seconds = round(time.perf_counter() - total_start, 3)

        return {
            "query": query,
            "query_profile": query_profile.to_dict(),
            "tickers": selected_tickers,
            "performance": {
                "total_seconds": total_seconds,
                "agent_seconds": timings,
                "retrieval_top_k": retrieval_top_k,
            },
            "agents": {
                "retriever": retrieval,
                "sentiment": sentiment,
                "risk": risk,
                "forecast": forecast,
                "decision": decision,
                "explainability": explanation,
            },
            "final_report": explanation.data["report_markdown"],
        }

    def _extract_tickers(self, query: str) -> List[str]:
        candidates = re.findall(r"\b[A-Z]{1,5}\b", query.upper())
        ignored = {
            "A", "AI", "AM", "AND", "ARE", "BUY", "CAN", "DAYS", "ETF", "FOR",
            "HAVE", "HOLD", "I", "IN", "INVEST", "IS", "LLM", "ME", "ML",
            "MY", "NEXT", "NOW", "OR", "PDF", "RAG", "RIGHT", "SAFER", "SEC",
            "SELL", "SHOULD", "THE", "TO", "USD", "USA", "VS", "WHERE",
            "WHICH", "YOU",
        }
        valid_tickers = self._known_tickers()
        tickers = []
        for candidate in candidates:
            if candidate in ignored:
                continue
            if valid_tickers and candidate not in valid_tickers:
                continue
            tickers.append(candidate)
        return list(dict.fromkeys(tickers))

    def _default_tickers(self, query: str, query_profile: QueryProfile | None = None) -> List[str]:
        query_profile = query_profile or self.query_intelligence.classify(query)
        if query_profile.needs_allocation or self._is_broad_investment_query(query):
            ranked = self._ranked_recommendation_tickers(query_profile.risk_profile)
            if ranked:
                return ranked[:5]
        return ["AAPL", "MSFT", "NVDA"]

    def _is_broad_investment_query(self, query: str) -> bool:
        text = query.lower()
        intent_terms = ["where", "what", "which", "recommend", "suggest", "should"]
        finance_terms = ["invest", "investment", "portfolio", "buy", "allocate"]
        budget_terms = ["$", "usd", "dollar", "money", "amount"]
        return (
            any(term in text for term in finance_terms)
            and (
                any(term in text for term in intent_terms)
                or any(term in text for term in budget_terms)
            )
        )

    def _known_tickers(self) -> set[str]:
        tickers: set[str] = set()
        for path, column in [
            (self.settings.processed_data_dir / "us_equity_universe.csv", "ticker"),
            (self.settings.data_root / "comprehensive_investment_report.csv", "Ticker"),
        ]:
            if not path.exists():
                continue
            try:
                with open(path, newline="", encoding="utf-8") as file:
                    for row in csv.DictReader(file):
                        value = str(row.get(column, "")).upper().strip()
                        if value:
                            tickers.add(value)
            except OSError:
                continue
        return tickers

    def _ranked_recommendation_tickers(self, risk_profile: str = "balanced") -> List[str]:
        path = self.settings.data_root / "comprehensive_investment_report.csv"
        if not path.exists():
            return []

        rows = []
        try:
            with open(path, newline="", encoding="utf-8") as file:
                for row in csv.DictReader(file):
                    ticker = str(row.get("Ticker", "")).upper().strip()
                    if not ticker:
                        continue
                    try:
                        score = float(row.get("Overall Score", 0) or 0)
                    except ValueError:
                        score = 0.0
                    risk = str(row.get("Risk Level", "")).lower()
                    if risk_profile == "conservative":
                        risk_penalty = 24.0 if risk == "high" else 7.0 if risk == "medium" else 0.0
                    elif risk_profile == "aggressive":
                        risk_penalty = 5.0 if risk == "high" else 1.0 if risk == "medium" else 0.0
                    else:
                        risk_penalty = 12.0 if risk == "high" else 4.0 if risk == "medium" else 0.0
                    rows.append((score - risk_penalty, ticker))
        except OSError:
            return []

        rows.sort(reverse=True)
        return [ticker for _, ticker in rows]

    def _default_document_paths(self) -> List[str]:
        docs_dir = self.project_root / "docs"
        paths = [
            self.project_root / "README.md",
            docs_dir / "EXECUTIVE_SUMMARY.md",
            docs_dir / "DATA_LAYER_EXPANSION.md",
            docs_dir / "DAY1_SUMMARY.md",
            docs_dir / "QUICK_START.md",
        ]
        return [str(path) for path in paths if path.exists()]
