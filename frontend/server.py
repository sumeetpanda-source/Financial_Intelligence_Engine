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
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents import OrchestratorAgent
from config import get_settings

SETTINGS = get_settings(PROJECT_ROOT)
DATA_DIR = SETTINGS.data_root
PROCESSED_DIR = SETTINGS.processed_data_dir
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
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "service": "financial-intelligence-engine",
        "environment": SETTINGS.environment,
        "genai_provider": SETTINGS.genai_provider,
        "genai_configured": SETTINGS.genai_provider != "openai" or bool(SETTINGS.openai_api_key),
        "checks": checks,
    }


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


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
    model_metrics = {}
    if model_metrics_path.exists():
        model_metrics = json.loads(model_metrics_path.read_text(encoding="utf-8"))

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
        "deep_analysis_count": int(len(recommendations)),
        "news_count": int(len(news)),
        "technical_count": int(len(technical)),
        "environment": SETTINGS.environment,
        "genai_provider": SETTINGS.genai_provider,
        "model_metrics": model_metrics,
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


def ask_investment_question(question: str) -> dict:
    tickers = extract_tickers(question)
    orchestrator = OrchestratorAgent(PROJECT_ROOT)
    result = orchestrator.run(question, tickers=tickers or None)
    decision = result["agents"]["decision"]
    forecast = result["agents"]["forecast"]
    risk = result["agents"]["risk"]
    sentiment = result["agents"]["sentiment"]
    retrieval = result["agents"]["retriever"]
    explainability = result["agents"]["explainability"]

    return {
        "question": question,
        "tickers": result["tickers"],
        "answer": result["final_report"],
        "suggestions": summarize_decisions(decision.data),
        "evidence": summarize_evidence(retrieval.evidence),
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
            if not question:
                self.send_json({"error": "Question is required."}, status=400)
                return
            self.send_json(ask_investment_question(question))
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
