"""
Tests for the Phase 1 multi-agent baseline.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import OrchestratorAgent


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
