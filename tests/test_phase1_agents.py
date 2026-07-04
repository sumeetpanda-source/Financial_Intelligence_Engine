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
