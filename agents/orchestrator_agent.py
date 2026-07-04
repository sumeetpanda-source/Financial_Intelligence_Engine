"""
Orchestrator Agent for the Phase 1 application.
"""

import re
from pathlib import Path
from typing import Iterable, List, Optional

from config import get_settings
from genai_layer import build_genai_provider

from .decision_agent import DecisionAgent
from .explainability_agent import ExplainabilityAgent
from .forecast_agent import ForecastAgent
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

    def run(
        self,
        query: str,
        tickers: Optional[Iterable[str]] = None,
        document_paths: Optional[Iterable[str]] = None,
    ) -> dict:
        selected_tickers = list(tickers or self._extract_tickers(query) or ["AAPL", "MSFT", "NVDA"])
        selected_documents = list(document_paths or self._default_document_paths())

        retrieval = self.retriever.run(query=query, document_paths=selected_documents)
        sentiment = self.sentiment.run(selected_tickers, retrieval.evidence)
        risk = self.risk.run(selected_tickers, sentiment.data["tickers"])
        forecast = self.forecast.run(selected_tickers)
        decision = self.decision.run(
            tickers=selected_tickers,
            sentiment_data=sentiment.data["tickers"],
            risk_data=risk.data["tickers"],
            forecast_data=forecast.data["tickers"],
        )
        explanation = self.explainability.run(
            query=query,
            tickers=selected_tickers,
            retrieved_evidence=retrieval.evidence,
            sentiment_data=sentiment.data["tickers"],
            risk_data=risk.data["tickers"],
            forecast_data=forecast.data["tickers"],
            decision_data=decision.data["tickers"],
        )

        return {
            "query": query,
            "tickers": selected_tickers,
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
        candidates = re.findall(r"\b[A-Z]{2,5}\b", query)
        ignored = {"RAG", "AI", "ML", "LLM", "ESG", "SEC", "PDF"}
        return [candidate for candidate in candidates if candidate not in ignored]

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
