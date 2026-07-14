"""
Explainability Agent.

Builds an examiner-friendly report with scores, rationale, limitations, and RAG
evidence. Hosted GenAI can later rewrite this report, but the baseline stays
auditable and deterministic.
"""

import re
from typing import Dict, Iterable, List

from genai_layer import GenAIProvider, build_genai_provider

from .schemas import AgentResult, EvidenceItem


class ExplainabilityAgent:
    """Creates a final report from all agent outputs."""

    def __init__(self, genai_provider: GenAIProvider | None = None):
        self.genai_provider = genai_provider or build_genai_provider()

    def run(
        self,
        query: str,
        tickers: Iterable[str],
        retrieved_evidence: List[EvidenceItem],
        sentiment_data: Dict[str, dict],
        risk_data: Dict[str, dict],
        forecast_data: Dict[str, dict],
        decision_data: Dict[str, dict],
    ) -> AgentResult:
        grounded_report_prompt = self._build_report(
            query=query,
            tickers=list(tickers),
            retrieved_evidence=retrieved_evidence,
            sentiment_data=sentiment_data,
            risk_data=risk_data,
            forecast_data=forecast_data,
            decision_data=decision_data,
        )
        report = self.genai_provider.generate_report(grounded_report_prompt)

        return AgentResult(
            agent_name="Explainability Agent",
            status="success",
            summary="Generated final explainable investment report.",
            data={"report_markdown": report},
            evidence=retrieved_evidence,
            confidence=0.76,
        )

    def _build_report(
        self,
        query: str,
        tickers: List[str],
        retrieved_evidence: List[EvidenceItem],
        sentiment_data: Dict[str, dict],
        risk_data: Dict[str, dict],
        forecast_data: Dict[str, dict],
        decision_data: Dict[str, dict],
    ) -> str:
        budget = self._extract_budget(query)
        allocation_intent = self._is_allocation_query(query)
        lines = [
            "# Phase 1 Financial Intelligence Report",
            "",
            f"User query: {query}",
            "",
            "## Architecture Used",
            "User Query -> Orchestrator Agent -> Retriever / Sentiment / Risk / Forecast Agents -> Decision Agent -> Explainability Agent -> Final Report",
            "",
            "## Response Guardrails",
            "- This is educational decision support, not personal financial advice.",
            "- The system ranks candidates using retrieved evidence, sentiment, risk, and forecast signals.",
            "- It should not recommend putting the full amount into one stock.",
            "- Weak or Hold-level signals should be treated as a watchlist, not a guaranteed buy.",
            "",
        ]

        if allocation_intent:
            lines.extend(
                [
                    "## Investment Question Handling",
                    "- Query type detected: broad investment/allocation question.",
                    f"- Candidate tickers analyzed: {', '.join(tickers)}.",
                    "- The answer is based on the current Phase 1 company universe and model outputs.",
                ]
            )
            if budget:
                lines.append(f"- Budget detected from question: ${budget:,.2f}.")
            lines.append("")

        lines.append("## Investment Decisions")

        for ticker in tickers:
            decision = decision_data.get(ticker, {})
            sentiment = sentiment_data.get(ticker, {})
            risk = risk_data.get(ticker, {})
            forecast = forecast_data.get(ticker, {})

            lines.extend(
                [
                    "",
                    f"### {ticker}",
                    f"- Recommendation: {decision.get('recommendation', 'N/A')}",
                    f"- Investment score: {decision.get('investment_score', 'N/A')}",
                    f"- Confidence: {decision.get('confidence', 'N/A')}",
                    f"- Sentiment: {sentiment.get('sentiment_label', 'N/A')} ({sentiment.get('sentiment_score', 'N/A')})",
                    f"- Risk: {risk.get('risk_level', 'N/A')} ({risk.get('risk_score', 'N/A')})",
                    f"- Forecast: {forecast.get('forecast_direction', 'N/A')} ({forecast.get('expected_return_pct', 'N/A')}% over {forecast.get('horizon_days', 'N/A')} days)",
                    "- Explanation: The decision combines sentiment, risk, and forecast signals using a transparent weighted scoring model.",
                ]
            )

        allocation_lines = self._allocation_section(
            budget=budget,
            allocation_intent=allocation_intent,
            decision_data=decision_data,
        )
        if allocation_lines:
            lines.extend(allocation_lines)

        lines.extend(["", "## Retrieved Evidence"])
        for idx, item in enumerate(retrieved_evidence, start=1):
            snippet = item.text[:260].strip()
            page = item.metadata.get("page_number")
            location = f", page {page}" if page else ""
            lines.extend(
                [
                    "",
                    f"{idx}. Source: {item.source}{location}",
                    f"   Relevance score: {item.score}",
                    f"   Evidence: {snippet}",
                ]
            )

        lines.extend(
            [
                "",
                "## Phase 1 Limitations",
                "- Local TF-IDF retrieval is used until the vector database is enabled.",
                "- Sentiment, risk, and forecast outputs are baseline signals until trained production models are connected.",
                "- GenAI uses a local deterministic fallback until a cloud provider API key is configured.",
                "- This report is decision support only and not financial advice.",
            ]
        )
        return "\n".join(lines)

    def _is_allocation_query(self, query: str) -> bool:
        text = query.lower()
        intent = any(
            phrase in text
            for phrase in [
                "where should i invest",
                "what should i invest",
                "which stock",
                "recommend",
                "allocate",
                "portfolio",
                "i have",
            ]
        )
        finance_context = any(term in text for term in ["invest", "buy", "stock", "portfolio", "$", "usd"])
        return intent and finance_context

    def _extract_budget(self, query: str) -> float | None:
        patterns = [
            r"\$\s*([0-9][0-9,]*(?:\.\d+)?)",
            r"\b([0-9][0-9,]*(?:\.\d+)?)\s*(?:usd|dollars?)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if not match:
                continue
            try:
                amount = float(match.group(1).replace(",", ""))
            except ValueError:
                continue
            if amount > 0:
                return amount
        return None

    def _allocation_section(
        self,
        budget: float | None,
        allocation_intent: bool,
        decision_data: Dict[str, dict],
    ) -> List[str]:
        if not allocation_intent:
            return []

        ranked = sorted(
            decision_data.items(),
            key=lambda item: float(item[1].get("investment_score", 0)),
            reverse=True,
        )
        if not ranked:
            return []

        eligible = [
            item for item in ranked
            if item[1].get("recommendation") not in {"Sell", "Strong Sell"}
        ]
        if not eligible:
            eligible = ranked[:3]

        has_buy_signal = any(
            item[1].get("recommendation") in {"Buy", "Strong Buy"}
            for item in eligible
        )
        reserve_pct = 0.10 if has_buy_signal else 0.25

        lines = [
            "",
            "## Budget-Aware Educational Allocation View",
        ]
        if budget:
            investable_budget = budget * (1 - reserve_pct)
            reserve_amount = budget - investable_budget
            total_score = sum(max(float(item[1].get("investment_score", 0)), 1.0) for item in eligible)
            lines.extend(
                [
                    f"- Total amount mentioned: ${budget:,.2f}.",
                    f"- Suggested reserve/watchlist cash: ${reserve_amount:,.2f} ({reserve_pct:.0%}).",
                    "- Candidate allocation is score-weighted across non-sell candidates.",
                    "",
                    "| Ticker | Recommendation | Score | Approx. allocation | Why |",
                    "|---|---:|---:|---:|---|",
                ]
            )
            for ticker, payload in eligible:
                score = max(float(payload.get("investment_score", 0)), 1.0)
                amount = investable_budget * score / total_score
                drivers = payload.get("drivers", {})
                why = (
                    f"sentiment {drivers.get('sentiment_score', 'N/A')}, "
                    f"risk {drivers.get('risk_score', 'N/A')}, "
                    f"expected return {drivers.get('expected_return_pct', 'N/A')}%"
                )
                lines.append(
                    f"| {ticker} | {payload.get('recommendation', 'N/A')} | "
                    f"{payload.get('investment_score', 'N/A')} | ${amount:,.2f} | {why} |"
                )
        else:
            lines.extend(
                [
                    "- No explicit budget was detected.",
                    "- Rank candidates by investment score and avoid concentrating the full amount in one company.",
                    "",
                    "| Ticker | Recommendation | Score |",
                    "|---|---:|---:|",
                ]
            )
            for ticker, payload in eligible:
                lines.append(
                    f"| {ticker} | {payload.get('recommendation', 'N/A')} | "
                    f"{payload.get('investment_score', 'N/A')} |"
                )

        if not has_buy_signal:
            lines.append(
                "- Note: Current signals are mostly Hold/watchlist level, so the conservative interpretation is staged entry or further research rather than aggressive buying."
            )
        return lines
