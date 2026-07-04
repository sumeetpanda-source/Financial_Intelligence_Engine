"""
Explainability Agent.

Builds an examiner-friendly report with scores, rationale, limitations, and RAG
evidence. Hosted GenAI can later rewrite this report, but the baseline stays
auditable and deterministic.
"""

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
        lines = [
            "# Phase 1 Financial Intelligence Report",
            "",
            f"User query: {query}",
            "",
            "## Architecture Used",
            "User Query -> Orchestrator Agent -> Retriever / Sentiment / Risk / Forecast Agents -> Decision Agent -> Explainability Agent -> Final Report",
            "",
            "## Investment Decisions",
        ]

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
