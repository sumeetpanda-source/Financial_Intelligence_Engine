"""
Phase 2 query intelligence.

This lightweight classifier keeps the Ask flow deterministic and auditable while
we move toward richer routing. It extracts user intent, budget, risk preference,
and horizon before the orchestrator calls specialist agents.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class QueryProfile:
    intent: str
    budget: float | None
    risk_profile: str
    horizon_days: int
    needs_allocation: bool
    needs_comparison: bool
    confidence: float
    rationale: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class QueryIntelligence:
    """Rule-based Phase 2 query classifier for transparent routing."""

    def classify(self, query: str) -> QueryProfile:
        text = query.lower()
        budget = self.extract_budget(query)
        horizon_days, horizon_reason = self._extract_horizon(text)
        risk_profile, risk_reason = self._extract_risk_profile(text)
        needs_allocation = self._has_any(text, ["invest", "allocate", "portfolio", "buy"]) and (
            budget is not None or self._has_any(text, ["where", "which", "suggest", "recommend"])
        )
        needs_comparison = self._has_any(text, ["compare", "versus", " vs ", "safer", "better", "between"])

        intent = "general_analysis"
        rationale = []
        if needs_allocation:
            intent = "budget_allocation"
            rationale.append("Detected allocation/investment wording.")
        elif needs_comparison:
            intent = "risk_comparison" if self._has_any(text, ["risk", "safer", "safe"]) else "ticker_comparison"
            rationale.append("Detected comparison wording.")
        elif self._has_any(text, ["risk", "volatile", "downside"]):
            intent = "risk_review"
            rationale.append("Detected risk-focused wording.")
        elif self._has_any(text, ["forecast", "return", "outlook", "next"]):
            intent = "forecast_review"
            rationale.append("Detected forecast/outlook wording.")
        elif self._has_any(text, ["sec", "filing", "10-k", "10-q", "rag", "document"]):
            intent = "document_research"
            rationale.append("Detected document/RAG research wording.")

        if budget is not None:
            rationale.append(f"Detected budget amount ${budget:,.2f}.")
        rationale.append(risk_reason)
        rationale.append(horizon_reason)

        confidence = 0.55
        if budget is not None:
            confidence += 0.15
        if intent != "general_analysis":
            confidence += 0.15
        if needs_comparison:
            confidence += 0.08
        if risk_profile != "balanced":
            confidence += 0.07

        return QueryProfile(
            intent=intent,
            budget=budget,
            risk_profile=risk_profile,
            horizon_days=horizon_days,
            needs_allocation=needs_allocation,
            needs_comparison=needs_comparison,
            confidence=round(min(confidence, 0.95), 2),
            rationale=rationale,
        )

    @staticmethod
    def extract_budget(query: str) -> float | None:
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

    def _extract_horizon(self, text: str) -> tuple[int, str]:
        day_match = re.search(r"\bnext\s+([0-9]{1,3})\s+days?\b", text)
        if day_match:
            return int(day_match.group(1)), f"Detected explicit {day_match.group(1)}-day horizon."
        month_match = re.search(r"\bnext\s+([0-9]{1,2})\s+months?\b", text)
        if month_match:
            months = int(month_match.group(1))
            return months * 30, f"Detected explicit {months}-month horizon."
        if self._has_any(text, ["long term", "long-term", "1 year", "one year"]):
            return 365, "Detected long-term horizon."
        if self._has_any(text, ["short term", "short-term", "near term", "near-term"]):
            return 30, "Detected short-term horizon."
        return 30, "Using default 30-day horizon."

    def _extract_risk_profile(self, text: str) -> tuple[str, str]:
        if self._has_any(text, ["safe", "safer", "conservative", "low risk", "less risky", "protect"]):
            return "conservative", "Detected conservative risk preference."
        if self._has_any(text, ["aggressive", "high growth", "higher return", "risk taking", "maximum return"]):
            return "aggressive", "Detected aggressive/growth risk preference."
        return "balanced", "Using balanced risk preference."

    @staticmethod
    def _has_any(text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)

