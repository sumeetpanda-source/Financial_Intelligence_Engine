"""
Local dashboard server for the Financial Intelligence Engine.

Run from the project root:
    python frontend/server.py
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
from threading import Lock
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents import OrchestratorAgent, QueryIntelligence
from config import get_settings

SETTINGS = get_settings(PROJECT_ROOT)
DATA_DIR = SETTINGS.data_root
PROCESSED_DIR = SETTINGS.processed_data_dir
QUERY_INTELLIGENCE = QueryIntelligence()
_ORCHESTRATOR: OrchestratorAgent | None = None
_ORCHESTRATOR_LOCK = Lock()
_CSV_CACHE: dict[str, tuple[float, pd.DataFrame]] = {}
OUTPUT_FILENAMES = {
    "comprehensive_fundamental_analysis.csv",
    "technical_indicators_summary.csv",
    "sentiment_analysis.csv",
    "financial_news_articles.csv",
    "comprehensive_investment_report.csv",
    "system_readiness_report.txt",
    "phase1_model_metrics.json",
}


def build_health() -> dict:
    checks = {
        "universe": (PROCESSED_DIR / "us_equity_universe.csv").exists(),
        "features": (SETTINGS.feature_store_dir / "phase1_model_features.csv").exists(),
        "risk_model": (SETTINGS.model_dir / "phase1_risk_model.pkl").exists(),
        "forecast_model": (SETTINGS.model_dir / "phase1_forecast_model.pkl").exists(),
        "vector_store": (SETTINGS.vector_store_dir / "chroma").exists(),
    }
    capabilities = {
        "real_market_data": (
            SETTINGS.processed_data_dir / "real_market_data_summary.json"
        ).exists(),
        "real_market_models": (
            SETTINGS.feature_store_dir / "real_market_latest_features.csv"
        ).exists(),
        "sec_filings": (
            SETTINGS.raw_data_dir / "sec_filings" / "ingestion_manifest.json"
        ).exists(),
    }
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "service": "financial-intelligence-engine",
        "environment": SETTINGS.environment,
        "genai_provider": SETTINGS.genai_provider,
        "genai_configured": SETTINGS.genai_provider != "openai" or bool(SETTINGS.openai_api_key),
        "checks": checks,
        "capabilities": capabilities,
    }


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    key = str(path.resolve())
    modified = path.stat().st_mtime
    cached = _CSV_CACHE.get(key)
    if cached and cached[0] == modified:
        return cached[1].copy()
    frame = pd.read_csv(path)
    _CSV_CACHE[key] = (modified, frame)
    return frame.copy()


def get_orchestrator() -> OrchestratorAgent:
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        with _ORCHESTRATOR_LOCK:
            if _ORCHESTRATOR is None:
                _ORCHESTRATOR = OrchestratorAgent(PROJECT_ROOT)
    return _ORCHESTRATOR


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def records(frame: pd.DataFrame, limit: int | None = None) -> list[dict]:
    if frame.empty:
        return []
    if limit is not None:
        frame = frame.head(limit)
    return frame.fillna("N/A").to_dict(orient="records")


def file_info(path: Path) -> dict:
    return {
        "name": path.name,
        "exists": path.exists(),
        "size_kb": round(path.stat().st_size / 1024, 1) if path.exists() else 0,
        "modified": path.stat().st_mtime if path.exists() else None,
        "url": f"/outputs/{path.name}" if path.exists() else None,
    }


def recommendation_distribution(frame: pd.DataFrame) -> dict:
    if frame.empty or "Recommendation" not in frame.columns:
        return {}
    return frame["Recommendation"].value_counts().to_dict()


def build_summary() -> dict:
    universe = read_csv(PROCESSED_DIR / "us_equity_universe.csv")
    recommendations = read_csv(DATA_DIR / "comprehensive_investment_report.csv")
    sentiment = read_csv(DATA_DIR / "sentiment_analysis.csv")
    technical = read_csv(DATA_DIR / "technical_indicators_summary.csv")
    news = read_csv(DATA_DIR / "financial_news_articles.csv")
    features = read_csv(DATA_DIR / "features" / "phase1_model_features.csv")
    model_metrics_path = SETTINGS.model_dir / "phase1_model_metrics.json"
    model_metrics = read_json(model_metrics_path)
    real_market_summary = read_json(PROCESSED_DIR / "real_market_data_summary.json")
    sec_manifest = read_json(DATA_DIR / "raw" / "sec_filings" / "ingestion_manifest.json")

    top_recommendations = recommendations
    if not recommendations.empty and "Overall Score" in recommendations.columns:
        top_recommendations = recommendations.sort_values("Overall Score", ascending=False)

    sentiment_leaders = sentiment
    if not sentiment.empty and "avg_sentiment" in sentiment.columns:
        sentiment_leaders = sentiment.sort_values("avg_sentiment", ascending=False)

    output_files = [
        DATA_DIR / "comprehensive_fundamental_analysis.csv",
        DATA_DIR / "technical_indicators_summary.csv",
        DATA_DIR / "sentiment_analysis.csv",
        DATA_DIR / "financial_news_articles.csv",
        DATA_DIR / "comprehensive_investment_report.csv",
        DATA_DIR / "system_readiness_report.txt",
        SETTINGS.model_dir / "phase1_model_metrics.json",
    ]

    return {
        "universe_count": int(len(universe)),
        "feature_count": int(len(features)),
        "real_history_count": int(real_market_summary.get("history_rows", 0)),
        "real_training_count": int(real_market_summary.get("training_rows", 0)),
        "real_ticker_count": int(real_market_summary.get("ticker_count", 0)),
        "sec_filing_count": int(sec_manifest.get("downloaded_count", 0)),
        "deep_analysis_count": int(len(recommendations)),
        "news_count": int(len(news)),
        "technical_count": int(len(technical)),
        "environment": SETTINGS.environment,
        "genai_provider": SETTINGS.genai_provider,
        "model_metrics": model_metrics,
        "real_market_summary": real_market_summary,
        "sec_ingestion": sec_manifest,
        "recommendation_distribution": recommendation_distribution(recommendations),
        "top_recommendations": records(top_recommendations, 5),
        "sentiment_leaders": records(sentiment_leaders, 5),
        "output_files": [file_info(path) for path in output_files],
    }


def get_universe(query: dict[str, list[str]]) -> dict:
    frame = read_csv(PROCESSED_DIR / "us_equity_universe.csv")
    search = query.get("q", [""])[0].strip().lower()
    limit = int(query.get("limit", ["1000"])[0])

    if search and not frame.empty:
        ticker = frame.get("ticker", pd.Series(dtype=str)).astype(str).str.lower()
        company = frame.get("company_name", pd.Series(dtype=str)).astype(str).str.lower()
        frame = frame[ticker.str.contains(search, na=False) | company.str.contains(search, na=False)]

    return {"count": int(len(frame)), "rows": records(frame, limit)}


def get_recommendations() -> dict:
    frame = read_csv(DATA_DIR / "comprehensive_investment_report.csv")
    if not frame.empty and "Overall Score" in frame.columns:
        frame = frame.sort_values("Overall Score", ascending=False)
    return {"rows": records(frame, 100)}


def get_sentiment() -> dict:
    frame = read_csv(DATA_DIR / "sentiment_analysis.csv")
    if not frame.empty and "avg_sentiment" in frame.columns:
        frame = frame.sort_values("avg_sentiment", ascending=False)
    return {"rows": records(frame, 100)}


def get_news(query: dict[str, list[str]]) -> dict:
    frame = read_csv(DATA_DIR / "financial_news_articles.csv")
    limit = int(query.get("limit", ["40"])[0])
    if not frame.empty and "date" in frame.columns:
        frame = frame.sort_values("date", ascending=False)
    return {"rows": records(frame, limit)}


def extract_tickers(question: str) -> list[str]:
    ignored = {
        "A", "AI", "AM", "AND", "ARE", "BUY", "CAN", "DAYS", "ETF", "FOR", "HOLD",
        "I", "IN", "INVEST", "IS", "LLM", "ME", "ML", "MY", "NEXT", "NOW", "OR",
        "PDF", "RAG", "RIGHT", "SAFER", "SEC", "SELL", "SHOULD", "THE", "TO",
        "USA", "VS", "WHICH", "YOU",
    }
    universe = read_csv(PROCESSED_DIR / "us_equity_universe.csv")
    valid_tickers = set()
    if not universe.empty and "ticker" in universe.columns:
        valid_tickers = set(universe["ticker"].dropna().astype(str).str.upper())
    for filename, column in [
        ("comprehensive_investment_report.csv", "Ticker"),
        ("technical_indicators_summary.csv", "Ticker"),
        ("sentiment_analysis.csv", "ticker"),
    ]:
        frame = read_csv(DATA_DIR / filename)
        if not frame.empty and column in frame.columns:
            valid_tickers.update(frame[column].dropna().astype(str).str.upper())

    tickers = []
    for item in re.findall(r"\b[A-Z]{1,5}\b", question.upper()):
        if item in ignored:
            continue
        if valid_tickers and item not in valid_tickers:
            continue
        tickers.append(item)
    return list(dict.fromkeys(tickers))[:5]


def summarize_decisions(decision_data: dict) -> list[dict]:
    tickers = decision_data.get("tickers", {}) if decision_data else {}
    return [
        {
            "ticker": ticker,
            "recommendation": payload.get("recommendation", "Hold"),
            "investment_score": payload.get("investment_score", 0),
            "confidence": payload.get("confidence", 0),
            "drivers": payload.get("drivers", {}),
        }
        for ticker, payload in tickers.items()
    ]


def summarize_evidence(evidence_items) -> list[dict]:
    return [
        {
            "source": item.source,
            "filename": item.metadata.get("filename", Path(item.source).name),
            "document_type": item.metadata.get("document_type", "document"),
            "page_number": item.metadata.get("page_number"),
            "score": item.score,
            "snippet": item.text[:360].strip(),
        }
        for item in evidence_items
    ]


def extract_budget_amount(question: str) -> float | None:
    return QUERY_INTELLIGENCE.extract_budget(question)


def parse_portfolio_holdings(portfolio_text: str, question: str = "") -> list[dict]:
    ownership_terms = ["i own", "i hold", "my portfolio", "currently own", "currently hold", "holding"]
    question_context = question if any(term in (question or "").lower() for term in ownership_terms) else ""
    raw = f"{portfolio_text or ''} {question_context or ''}".upper()
    if not raw.strip():
        return []

    ignored = {
        "A", "AI", "AM", "AND", "ARE", "BUY", "CAN", "DAYS", "ETF", "FOR",
        "HAVE", "HOLD", "I", "IN", "INVEST", "IS", "ME", "MY", "NOW", "OR",
        "SELL", "SHARE", "SHARES", "SHOULD", "STOCK", "STOCKS", "THE", "TO",
        "USD", "VS", "WHERE", "WHICH", "WHY", "YOU",
    }
    holdings: dict[str, dict] = {}
    for ticker, dollar_marker, value in re.findall(r"\b([A-Z]{1,5})\b(?:\s*(?:[:=X-]|SHARES?|WORTH)?\s*(\$?)(\d+(?:\.\d+)?))?", raw):
        if ticker in ignored:
            continue
        if ticker not in holdings:
            holdings[ticker] = {"ticker": ticker, "quantity": None, "market_value": None, "raw": ticker}
        if value:
            if dollar_marker == "$":
                holdings[ticker]["market_value"] = float(value)
                holdings[ticker]["raw"] = f"{ticker} ${value}"
            else:
                holdings[ticker]["quantity"] = float(value)
                holdings[ticker]["raw"] = f"{ticker} {value}"
    return list(holdings.values())[:12]


def format_usd(amount: float | int | None) -> str:
    if amount is None:
        return "the provided budget"
    return f"${float(amount):,.2f}"


def simple_signal_label(recommendation: str) -> str:
    text_value = (recommendation or "").lower()
    if "buy" in text_value:
        return "Consider"
    if "sell" in text_value:
        return "Avoid"
    return "Watch"


def simple_reason(item: dict) -> str:
    drivers = item.get("drivers", {})
    risk = drivers.get("risk_score", "N/A")
    expected_return = drivers.get("expected_return_pct", "N/A")
    recommendation = item.get("recommendation", "Hold")
    if "Buy" in recommendation:
        return f"Better current signal with risk score {risk} and expected return {expected_return}%."
    if "Sell" in recommendation:
        return f"Excluded because the current model signal is {recommendation}."
    return f"Hold-level signal, so use only as a watchlist or small staged entry."


def build_user_friendly_answer(
    question: str,
    suggestions: list[dict],
    query_profile: dict | None = None,
    portfolio_text: str = "",
) -> dict:
    query_profile = query_profile or QUERY_INTELLIGENCE.classify(question).to_dict()
    budget = query_profile.get("budget")
    risk_profile = query_profile.get("risk_profile", "balanced")
    horizon_days = int(query_profile.get("horizon_days") or 30)
    ranked = sorted(
        suggestions,
        key=lambda item: float(item.get("investment_score") or 0),
        reverse=True,
    )
    eligible = [
        item for item in ranked
        if item.get("recommendation") not in {"Sell", "Strong Sell"}
    ]
    buy_signals = [
        item for item in eligible
        if item.get("recommendation") in {"Buy", "Strong Buy"}
    ]
    best = eligible[0] if eligible else ranked[0] if ranked else {}
    has_strong_signal = bool(buy_signals)
    portfolio_holdings = parse_portfolio_holdings(portfolio_text, question)

    if not ranked:
        return {
            "headline": "I could not generate a reliable investment view from the current data.",
            "stance": "No decision",
            "primary_action": "No allocation suggested",
            "allocation_title": "No Investable Plan",
            "budget": budget,
            "reserve_amount": budget,
            "allocations": [],
            "portfolio": {
                "holdings": portfolio_holdings,
                "overlap_with_plan": [],
                "message": "No current portfolio was provided." if not portfolio_holdings else "Portfolio holdings were detected from your input.",
            },
            "summary_cards": [
                {
                    "label": "Decision",
                    "value": "Wait",
                    "detail": "No scored candidates were returned.",
                }
            ],
            "key_points": [
                "No scored candidates were returned by the agent workflow.",
                "Try asking with specific tickers such as AAPL, MSFT, JPM, or JNJ.",
            ],
            "methodology": [
                "The system only answers from available model signals and retrieved evidence.",
            ],
            "next_steps": [
                "Ask again with specific ticker symbols or a preferred risk profile.",
                "Refresh market data before making any real investment decision.",
            ],
            "risk_note": "No allocation is suggested without scored candidates.",
        }

    if has_strong_signal:
        stance = "Selective buy signal"
        headline = "The current signals support a diversified, limited allocation."
        reserve_ratio = 0.25 if risk_profile == "conservative" else 0.15 if risk_profile == "aggressive" else 0.20
    elif eligible:
        stance = "Watchlist / cautious entry"
        headline = (
            "Current signals are not strong enough for an aggressive buy. Treat this as a cautious "
            "watchlist decision, not a full-investment recommendation."
        )
        base_reserve = 0.75 if len(eligible) == 1 else 0.70
        reserve_ratio = min(base_reserve + 0.10, 0.90) if risk_profile == "conservative" else max(base_reserve - 0.10, 0.40) if risk_profile == "aggressive" else base_reserve
    else:
        stance = "Stay in cash / avoid for now"
        headline = (
            "I would avoid investing this amount in the analyzed stocks right now because the "
            "available signals are Sell-level."
        )
        reserve_ratio = 1.0

    allocation_budget = 0.0 if budget is None else budget * (1 - reserve_ratio)
    if budget is not None and eligible and not has_strong_signal and len(eligible) == 1:
        allocation_budget = min(allocation_budget, budget * 0.25)

    allocation_candidates = buy_signals or eligible[:3]
    if budget is not None and len(allocation_candidates) == 1:
        single_stock_cap = 0.25 if risk_profile == "conservative" else 0.50 if risk_profile == "aggressive" else 0.35
        allocation_budget = min(allocation_budget, budget * single_stock_cap)
    score_total = sum(
        max(float(item.get("investment_score") or 0), 1.0)
        for item in allocation_candidates
    )
    allocations = []
    if budget is not None and allocation_budget > 0 and score_total > 0:
        for item in allocation_candidates:
            score = max(float(item.get("investment_score") or 0), 1.0)
            amount = allocation_budget * score / score_total
            drivers = item.get("drivers", {})
            allocations.append(
                {
                    "ticker": item.get("ticker"),
                    "amount": round(amount, 2),
                    "recommendation": item.get("recommendation"),
                    "score": item.get("investment_score"),
                    "action": simple_signal_label(item.get("recommendation")),
                    "reason": simple_reason(item),
                }
            )

    if budget is None:
        reserve_amount = None
    else:
        reserve_amount = round(budget - sum(item["amount"] for item in allocations), 2)

    invested_amount = round(sum(item["amount"] for item in allocations), 2)
    allocated_tickers = {item.get("ticker") for item in allocations}
    portfolio_overlap = [
        item["ticker"]
        for item in portfolio_holdings
        if item["ticker"] in allocated_tickers
    ]
    if budget is not None and has_strong_signal:
        primary_action = (
            f"Invest up to {format_usd(invested_amount)} across the selected candidates and "
            f"keep {format_usd(reserve_amount)} as reserve."
        )
        allocation_title = "Suggested Allocation"
    elif budget is not None and eligible:
        primary_action = (
            f"Keep {format_usd(reserve_amount)} in reserve. If you still want market exposure, "
            f"stage only {format_usd(invested_amount)} across the watchlist names below."
        )
        allocation_title = "Cautious Watchlist Plan"
    elif budget is not None:
        primary_action = f"Keep {format_usd(reserve_amount)} in reserve and avoid the analyzed candidates for now."
        allocation_title = "Reserve Recommended"
    else:
        primary_action = "No budget was provided, so the system is ranking candidates without calculating dollar allocation."
        allocation_title = "Ranked View"

    if budget is not None and not has_strong_signal and eligible:
        headline = (
            f"I would not deploy the full {format_usd(budget)} right now. The current evidence is "
            "mostly Hold-level, so the safer demo output is a staged watchlist plan."
        )

    top_tickers = ", ".join(item.get("ticker", "") for item in ranked[:5])
    risk_text = f"{risk_profile} risk preference"
    key_points = [
        f"I treated this as a {risk_text} question over about {horizon_days} days.",
        f"I reviewed these candidates from the current model universe: {top_tickers}.",
        f"The strongest current candidate is {best.get('ticker', 'N/A')}, but the signal is {best.get('recommendation', 'N/A')}, not a guaranteed buy.",
        "I excluded Sell and Strong Sell names from any investable allocation.",
    ]
    if not has_strong_signal:
        key_points.append(
            "No strong Buy signal is present, so the system keeps a larger reserve instead of forcing a recommendation."
        )
    if portfolio_overlap:
        key_points.append(
            f"You already hold {', '.join(portfolio_overlap)}, so avoid adding too much concentration there."
        )

    return {
        "headline": headline,
        "stance": stance,
        "primary_action": primary_action,
        "allocation_title": allocation_title,
        "budget": budget,
        "reserve_amount": reserve_amount,
        "allocations": allocations,
        "portfolio": {
            "holdings": portfolio_holdings,
            "overlap_with_plan": portfolio_overlap,
            "message": (
                f"You already hold {', '.join(item['ticker'] for item in portfolio_holdings)}. "
                f"{', '.join(portfolio_overlap)} also appears in the suggested watchlist."
                if portfolio_overlap
                else "These are the holdings you provided for context."
                if portfolio_holdings
                else "No current portfolio was provided. Add holdings in the portfolio box to see overlap with new suggestions."
            ),
        },
        "summary_cards": [
            {
                "label": "Suggested action",
                "value": "Stage slowly" if eligible and not has_strong_signal else stance,
                "detail": "Avoid putting the full amount into one stock.",
            },
            {
                "label": "Cash reserve",
                "value": format_usd(reserve_amount) if budget is not None else "N/A",
                "detail": "Reserved because current signals are not guaranteed.",
            },
            {
                "label": "Best candidate",
                "value": best.get("ticker", "N/A"),
                "detail": f"{best.get('recommendation', 'N/A')} signal, score {best.get('investment_score', 'N/A')}.",
            },
        ],
        "key_points": key_points,
        "methodology": [
            "A Phase 2 query classifier detects intent, budget, risk preference, and investment horizon before routing.",
            "Candidate stocks are selected from the current scored company universe.",
            "Each candidate is evaluated using Sentiment, Risk, and Forecast agents.",
            "The Decision Agent combines 30% sentiment, 35% lower-risk contribution, and 35% forecast-return contribution.",
            "Budget allocation is capped when signals are weak to avoid overconfident advice.",
        ],
        "next_steps": [
            "Check latest news, earnings, and price movement before placing any real order.",
            "Use diversification and avoid investing the full amount in a single stock.",
            "Re-run the question after refreshing market and SEC filing data.",
        ],
        "risk_note": "Educational decision support only. This is not personal financial advice or a guarantee of returns.",
    }


def ask_investment_question(question: str, portfolio_text: str = "") -> dict:
    tickers = extract_tickers(question)
    orchestrator = get_orchestrator()
    result = orchestrator.run(question, tickers=tickers or None)
    decision = result["agents"]["decision"]
    forecast = result["agents"]["forecast"]
    risk = result["agents"]["risk"]
    sentiment = result["agents"]["sentiment"]
    retrieval = result["agents"]["retriever"]
    explainability = result["agents"]["explainability"]

    suggestions = summarize_decisions(decision.data)
    query_profile = result.get("query_profile", QUERY_INTELLIGENCE.classify(question).to_dict())

    return {
        "question": question,
        "query_profile": query_profile,
        "tickers": result["tickers"],
        "portfolio_input": portfolio_text,
        "answer": result["final_report"],
        "user_answer": build_user_friendly_answer(question, suggestions, query_profile, portfolio_text),
        "suggestions": suggestions,
        "evidence": summarize_evidence(retrieval.evidence),
        "performance": result.get("performance", {}),
        "agent_summaries": [
            {"agent": retrieval.agent_name, "summary": retrieval.summary, "confidence": retrieval.confidence},
            {"agent": sentiment.agent_name, "summary": sentiment.summary, "confidence": sentiment.confidence},
            {"agent": risk.agent_name, "summary": risk.summary, "confidence": risk.confidence},
            {"agent": forecast.agent_name, "summary": forecast.summary, "confidence": forecast.confidence},
            {"agent": decision.agent_name, "summary": decision.summary, "confidence": decision.confidence},
            {
                "agent": explainability.agent_name,
                "summary": explainability.summary,
                "confidence": explainability.confidence,
            },
        ],
        "disclaimer": "Educational analysis only. This is not financial advice.",
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/ask":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body or "{}")
            question = str(payload.get("question", "")).strip()
            portfolio_text = str(payload.get("portfolio", "")).strip()
            if not question:
                self.send_json({"error": "Question is required."}, status=400)
                return
            self.send_json(ask_investment_question(question, portfolio_text))
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def do_GET(self):
        self.handle_request(send_body=True)

    def do_HEAD(self):
        self.handle_request(send_body=False)

    def handle_request(self, send_body: bool):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        routes = {
            "/health": build_health,
            "/api/health": build_health,
            "/api/summary": lambda: build_summary(),
            "/api/universe": lambda: get_universe(query),
            "/api/recommendations": get_recommendations,
            "/api/sentiment": get_sentiment,
            "/api/news": lambda: get_news(query),
        }

        if parsed.path in routes:
            self.send_json(routes[parsed.path](), send_body=send_body)
            return

        if parsed.path.startswith("/outputs/"):
            self.serve_output_file(parsed.path, send_body=send_body)
            return

        self.serve_static(parsed.path, send_body=send_body)

    def send_json(self, payload: dict, send_body: bool = True, status: int = 200):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def serve_output_file(self, request_path: str, send_body: bool = True):
        filename = Path(request_path).name
        if filename not in OUTPUT_FILENAMES:
            self.send_error(404)
            return

        base_dir = SETTINGS.model_dir if filename == "phase1_model_metrics.json" else DATA_DIR
        path = (base_dir / filename).resolve()
        if not str(path).startswith(str(base_dir)) or not path.exists():
            self.send_error(404)
            return

        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Disposition", f'inline; filename="{path.name}"')
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def serve_static(self, request_path: str, send_body: bool = True):
        relative = "index.html" if request_path in {"/", ""} else request_path.lstrip("/")
        path = (FRONTEND_DIR / relative).resolve()

        if not str(path).startswith(str(FRONTEND_DIR)) or not path.exists() or path.is_dir():
            self.send_error(404)
            return

        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)


def main():
    host = os.getenv("FIE_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
