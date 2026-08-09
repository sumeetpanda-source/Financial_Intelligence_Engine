"""
Tests for the Phase 1 multi-agent baseline.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import OrchestratorAgent
from agents.explainability_agent import ExplainabilityAgent


class HallucinatingProvider:
    def generate_report(self, prompt: str) -> str:
        return "Put all $5000 into FAKE because it is guaranteed to go up."


def test_phase1_orchestrator_generates_report():
    orchestrator = OrchestratorAgent()
    result = orchestrator.run(
        query="Should I invest in AAPL and MSFT for the next 30 days?",
        tickers=["AAPL", "MSFT"],
    )

    assert result["tickers"] == ["AAPL", "MSFT"]
    assert "final_report" in result
    assert "Phase 1 Financial Intelligence Report" in result["final_report"]
    assert "decision" in result["agents"]
    assert result["agents"]["decision"].status == "success"


def test_broad_budget_question_generates_allocation_view():
    orchestrator = OrchestratorAgent()
    result = orchestrator.run(
        query="Where should I invest if I have $5000?",
    )

    assert len(result["tickers"]) >= 3
    assert result["tickers"] != ["AAPL", "MSFT", "NVDA"]
    assert "Budget-Aware Educational Allocation View" in result["final_report"]
    assert "$5,000.00" in result["final_report"]
    assert "Candidate tickers analyzed" in result["final_report"]
    assert "not personal financial advice" in result["final_report"]
    assert "How The Suggestion Was Calculated" in result["final_report"]


def test_budget_question_bypasses_hallucinating_genai_provider():
    agent = ExplainabilityAgent(HallucinatingProvider())
    result = agent.run(
        query="I have $5000, in which stock should I invest?",
        tickers=["AAPL"],
        retrieved_evidence=[],
        sentiment_data={"AAPL": {"sentiment_label": "Neutral", "sentiment_score": 0.55}},
        risk_data={"AAPL": {"risk_level": "Medium", "risk_score": 50}},
        forecast_data={
            "AAPL": {
                "forecast_direction": "Flat",
                "expected_return_pct": 0.2,
                "horizon_days": 30,
            }
        },
        decision_data={
            "AAPL": {
                "recommendation": "Hold",
                "investment_score": 52.0,
                "confidence": 0.52,
                "drivers": {
                    "sentiment_score": 0.55,
                    "risk_score": 50,
                    "expected_return_pct": 0.2,
                },
            }
        },
    )

    report = result.data["report_markdown"]
    assert "FAKE" not in report
    assert "guaranteed to go up" not in report
    assert "Budget-Aware Educational Allocation View" in report
    assert "Suggested reserve/watchlist cash: $3,750.00" in report
    assert result.warnings == [
        "Strict grounded mode used for budget/allocation question to reduce hallucination."
    ]
