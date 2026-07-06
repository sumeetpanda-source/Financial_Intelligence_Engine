"""Tests for SEC filing discovery, storage, and RAG metadata."""

import json

import pytest

from rag_layer.document_loader import DocumentLoader
from rag_layer.sec_filings import SECFilingIngestor


class FakeResponse:
    def __init__(self, payload=None, text="", status_code=200):
        self.payload = payload
        self.text = text
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, submissions, filing_html):
        self.submissions = submissions
        self.filing_html = filing_html
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "submissions" in url:
            return FakeResponse(payload=self.submissions)
        return FakeResponse(text=self.filing_html)


def test_sec_filing_ingestion_writes_source_metadata(tmp_path):
    submissions = {
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q"],
                "filingDate": ["2025-10-31", "2025-08-01"],
                "reportDate": ["2025-09-27", "2025-06-28"],
                "accessionNumber": ["0000320193-25-000079", "0000320193-25-000055"],
                "primaryDocument": ["aapl-20250927.htm", "aapl-20250628.htm"],
            }
        },
    }
    session = FakeSession(
        submissions=submissions,
        filing_html="<html><body><h1>Annual Report</h1><p>" + ("Revenue and risk. " * 100) + "</p></body></html>",
    )
    ingestor = SECFilingIngestor(
        user_agent="FinancialIntelligenceEngine/1.0 test@example.com",
        session=session,
        request_interval_seconds=0,
    )
    ingestor.raw_dir = tmp_path / "sec_filings"
    ingestor.ticker_file = tmp_path / "company_tickers.json"
    ingestor.ticker_file.write_text(
        json.dumps({"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}),
        encoding="utf-8",
    )

    records = ingestor.list_recent_filings("AAPL", forms=["10-K"], per_form=1)
    path = ingestor.download_filing(records[0])
    metadata = DocumentLoader.infer_metadata(path)

    assert path.exists()
    assert metadata["ticker"] == "AAPL"
    assert metadata["document_type"] == "10-K"
    assert metadata["filing_date"] == "2025-10-31"
    assert metadata["accession_number"] == "0000320193-25-000079"
    assert metadata["source"].startswith("https://www.sec.gov/Archives/")
    assert session.calls[0][1]["headers"]["User-Agent"].endswith("test@example.com")


def test_sec_ingestion_requires_identifiable_user_agent():
    ingestor = SECFilingIngestor(user_agent="", session=FakeSession({}, ""))
    with pytest.raises(ValueError, match="FIE_SEC_USER_AGENT"):
        ingestor.list_recent_filings("AAPL")
