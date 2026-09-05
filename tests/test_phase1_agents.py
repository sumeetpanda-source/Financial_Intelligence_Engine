"""
Tests for the Phase 1 multi-agent baseline.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import OrchestratorAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.query_intelligence import QueryIntelligence
from frontend.server import (
    ask_investment_question,
    build_user_friendly_answer,
    parse_portfolio_holdings,
)


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


def test_user_friendly_answer_keeps_weak_signals_conservative():
    answer = build_user_friendly_answer(
        "If I want to invest $1000, where should I invest?",
        [
            {
                "ticker": "AAPL",
                "recommendation": "Hold",
                "investment_score": 50.0,
                "drivers": {
                    "sentiment_score": 0.47,
                    "risk_score": 50,
                    "expected_return_pct": 0.59,
                },
            }
        ],
    )

    assert answer["stance"] == "Watchlist / cautious entry"
    assert answer["budget"] == 1000.0
    assert answer["reserve_amount"] == 750.0
    assert answer["allocations"][0]["amount"] == 250.0
    assert "not personal financial advice" in answer["risk_note"]


def test_phase2_query_intelligence_extracts_intent_budget_and_horizon():
    profile = QueryIntelligence().classify(
        "I am a conservative investor with $2500. Where should I invest for the next 3 months?"
    )

    assert profile.intent == "budget_allocation"
    assert profile.budget == 2500.0
    assert profile.risk_profile == "conservative"
    assert profile.horizon_days == 90
    assert profile.needs_allocation is True
    assert profile.confidence >= 0.85


def test_orchestrator_uses_query_profile_for_forecast_horizon():
    result = OrchestratorAgent().run(
        "Compare AAPL and MSFT for the next 90 days.",
        tickers=["AAPL", "MSFT"],
    )

    assert result["query_profile"]["horizon_days"] == 90
    for forecast in result["agents"]["forecast"].data["tickers"].values():
        assert forecast["horizon_days"] == 90


def test_user_friendly_answer_uses_conservative_risk_profile():
    answer = build_user_friendly_answer(
        "I am conservative and want to invest $1000. Where should I invest?",
        [
            {
                "ticker": "AAPL",
                "recommendation": "Hold",
                "investment_score": 50.0,
                "drivers": {
                    "sentiment_score": 0.47,
                    "risk_score": 50,
                    "expected_return_pct": 0.59,
                },
            }
        ],
        {
            "intent": "budget_allocation",
            "budget": 1000.0,
            "risk_profile": "conservative",
            "horizon_days": 30,
        },
    )

    assert answer["reserve_amount"] == 850.0
    assert answer["allocations"][0]["amount"] == 150.0
    assert "conservative risk preference" in answer["key_points"][0]


def test_user_friendly_answer_caps_single_stock_buy_allocation():
    answer = build_user_friendly_answer(
        "If I want to invest $1000, where should I invest?",
        [
            {
                "ticker": "PFE",
                "recommendation": "Buy",
                "investment_score": 62.22,
                "drivers": {
                    "sentiment_score": 0.58,
                    "risk_score": 50,
                    "expected_return_pct": 2.7,
                },
            }
        ],
    )

    assert answer["allocations"][0]["amount"] == 350.0
    assert answer["reserve_amount"] == 650.0
    assert "putting the full amount into one stock" in answer["summary_cards"][0]["detail"]


def test_user_friendly_answer_includes_user_portfolio_context():
    answer = build_user_friendly_answer(
        "I have $1000. Where should I invest?",
        [
            {
                "ticker": "JPM",
                "recommendation": "Hold",
                "investment_score": 55.0,
                "drivers": {
                    "sentiment_score": 0.45,
                    "risk_score": 25,
                    "expected_return_pct": 0.7,
                },
            }
        ],
        portfolio_text="AAPL 5 shares, MSFT $800",
    )

    assert answer["portfolio"]["holdings"][0]["ticker"] == "AAPL"
    assert answer["portfolio"]["holdings"][1]["ticker"] == "MSFT"
    assert answer["portfolio"]["holdings"][0]["quantity"] == 5.0
    assert answer["portfolio"]["holdings"][1]["market_value"] == 800.0
    assert "provided for context" in answer["portfolio"]["message"]


def test_portfolio_parser_does_not_treat_comparison_question_as_holdings():
    holdings = parse_portfolio_holdings("", "Compare AAPL and MSFT")

    assert holdings == []


def test_ask_response_cache_serves_repeated_question():
    question = "I am conservative and have $1234. Where should I invest for review cache test?"
    portfolio = "AAPL 1 share"

    first = ask_investment_question(question, portfolio)
    second = ask_investment_question(question, portfolio)

    assert first["performance"]["response_cache_hit"] is False
    assert second["performance"]["response_cache_hit"] is True
    assert second["performance"]["total_seconds"] == 0.0
