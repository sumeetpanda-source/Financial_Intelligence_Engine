"""SEC EDGAR filing ingestion for the Phase 1 RAG corpus."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from config import get_settings


SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_ARCHIVE_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_compact}/{primary_document}"
)


@dataclass(frozen=True)
class FilingRecord:
    ticker: str
    cik: str
    company_name: str
    form: str
    filing_date: str
    report_date: str
    accession_number: str
    primary_document: str
    filing_url: str


class SECFilingIngestor:
    """Downloads official filing HTML as text with source-aware metadata."""

    def __init__(
        self,
        user_agent: str | None = None,
        session: requests.Session | None = None,
        request_interval_seconds: float = 0.15,
    ):
        self.settings = get_settings()
        self.user_agent = (user_agent or self.settings.sec_user_agent).strip()
        self.session = session or requests.Session()
        self.request_interval_seconds = max(float(request_interval_seconds), 0.0)
        self.raw_dir = self.settings.raw_data_dir / "sec_filings"
        self.ticker_file = (
            self.settings.raw_data_dir / "us_equities" / "company_tickers.json"
        )

    def ingest(
        self,
        tickers: Iterable[str],
        forms: Iterable[str] = ("10-K", "10-Q"),
        per_form: int = 1,
        refresh: bool = False,
    ) -> dict:
        self._require_user_agent()
        selected_tickers = self._normalize_values(tickers)
        selected_forms = self._normalize_values(forms)
        downloaded: list[dict] = []
        failures: list[dict] = []

        for ticker in selected_tickers:
            try:
                records = self.list_recent_filings(
                    ticker=ticker,
                    forms=selected_forms,
                    per_form=per_form,
                )
            except Exception as exc:
                failures.append({"ticker": ticker, "stage": "listing", "error": str(exc)})
                continue

            for record in records:
                try:
                    path = self.download_filing(record, refresh=refresh)
                    downloaded.append(
                        {
                            **asdict(record),
                            "local_path": str(path),
                        }
                    )
                except Exception as exc:
                    failures.append(
                        {
                            "ticker": ticker,
                            "form": record.form,
                            "accession_number": record.accession_number,
                            "stage": "download",
                            "error": str(exc),
                        }
                    )

        manifest = {
            "source": "SEC EDGAR",
            "tickers": selected_tickers,
            "forms": selected_forms,
            "per_form": int(per_form),
            "downloaded_count": len(downloaded),
            "downloaded": downloaded,
            "failures": failures,
        }
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        (self.raw_dir / "ingestion_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        return manifest

    def list_recent_filings(
        self,
        ticker: str,
        forms: Iterable[str] = ("10-K", "10-Q"),
        per_form: int = 1,
    ) -> list[FilingRecord]:
        self._require_user_agent()
        ticker_map = self._ticker_map()
        normalized_ticker = ticker.upper().strip()
        company = ticker_map.get(normalized_ticker)
        if not company:
            raise ValueError(f"Ticker {normalized_ticker} was not found in SEC company tickers.")

        cik = str(company["cik"]).zfill(10)
        payload = self._get_json(SEC_SUBMISSIONS_URL.format(cik=cik))
        recent = payload.get("filings", {}).get("recent", {})
        rows = self._columnar_rows(recent)
        selected_forms = self._normalize_values(forms)

        records: list[FilingRecord] = []
        for form in selected_forms:
            matching = [row for row in rows if str(row.get("form", "")).upper() == form]
            matching.sort(key=lambda row: str(row.get("filingDate", "")), reverse=True)
            for row in matching[: max(int(per_form), 0)]:
                accession = str(row.get("accessionNumber", ""))
                primary_document = str(row.get("primaryDocument", ""))
                if not accession or not primary_document:
                    continue
                records.append(
                    FilingRecord(
                        ticker=normalized_ticker,
                        cik=cik,
                        company_name=str(payload.get("name") or company["company_name"]),
                        form=form,
                        filing_date=str(row.get("filingDate", "")),
                        report_date=str(row.get("reportDate", "")),
                        accession_number=accession,
                        primary_document=primary_document,
                        filing_url=SEC_ARCHIVE_URL.format(
                            cik=int(cik),
                            accession_compact=accession.replace("-", ""),
                            primary_document=primary_document,
                        ),
                    )
                )
        return records

    def download_filing(self, record: FilingRecord, refresh: bool = False) -> Path:
        ticker_dir = self.raw_dir / record.ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{record.ticker}_{record.form}_{record.filing_date}_"
            f"{record.accession_number}.txt"
        )
        path = ticker_dir / filename
        metadata_path = path.with_suffix(path.suffix + ".metadata.json")
        if path.exists() and metadata_path.exists() and not refresh:
            return path

        response = self._get(record.filing_url)
        text = self._html_to_text(response.text)
        if len(text) < 1000:
            raise ValueError("SEC filing text was unexpectedly short.")

        metadata = {
            "source": record.filing_url,
            "local_path": str(path),
            "filename": filename,
            "document_type": record.form,
            "ticker": record.ticker,
            "company_name": record.company_name,
            "cik": record.cik,
            "filing_date": record.filing_date,
            "report_date": record.report_date,
            "year": int(record.filing_date[:4]),
            "accession_number": record.accession_number,
            "primary_document": record.primary_document,
            "filing_url": record.filing_url,
        }
        path.write_text(text, encoding="utf-8")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return path

    def _ticker_map(self) -> dict[str, dict]:
        if self.ticker_file.exists():
            payload = json.loads(self.ticker_file.read_text(encoding="utf-8"))
        else:
            payload = self._get_json(SEC_TICKERS_URL)
            self.ticker_file.parent.mkdir(parents=True, exist_ok=True)
            self.ticker_file.write_text(json.dumps(payload), encoding="utf-8")

        rows = payload.values() if isinstance(payload, dict) else payload
        return {
            str(row.get("ticker", "")).upper(): {
                "cik": row.get("cik_str"),
                "company_name": row.get("title", ""),
            }
            for row in rows
            if row.get("ticker") and row.get("cik_str") is not None
        }

    def _get_json(self, url: str) -> dict:
        return self._get(url).json()

    def _get(self, url: str):
        response = self.session.get(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json,text/html,*/*",
            },
            timeout=30,
        )
        response.raise_for_status()
        if self.request_interval_seconds:
            time.sleep(self.request_interval_seconds)
        return response

    def _require_user_agent(self):
        if not self.user_agent or "@" not in self.user_agent:
            raise ValueError(
                "Set FIE_SEC_USER_AGENT to an application name and contact email, "
                'for example "FinancialIntelligenceEngine/1.0 your@email.com".'
            )

    @staticmethod
    def _columnar_rows(columns: dict) -> list[dict]:
        if not columns:
            return []
        row_count = max((len(value) for value in columns.values() if isinstance(value, list)), default=0)
        return [
            {
                key: value[index] if isinstance(value, list) and index < len(value) else None
                for key, value in columns.items()
            }
            for index in range(row_count)
        ]

    @staticmethod
    def _html_to_text(html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())

    @staticmethod
    def _normalize_values(values: Iterable[str]) -> list[str]:
        normalized = [str(value).upper().strip() for value in values if str(value).strip()]
        return list(dict.fromkeys(normalized))
