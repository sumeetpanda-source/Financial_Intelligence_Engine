"""
US equities universe builder.

Phase 1 target: build a huge US equity universe from official/exchange files
when available, then cache the result locally. The module works offline if the
raw files are already present, and can fetch sources in cloud/local API runs.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests

from config import get_settings
from storage import DataStore


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


class USEquityUniverseBuilder:
    """Builds and caches a US equity ticker universe."""

    SEED_TICKERS = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "META",
        "TSLA",
        "JPM",
        "UNH",
        "XOM",
        "V",
        "MA",
        "PG",
        "JNJ",
        "HD",
        "COST",
        "ABBV",
        "BAC",
        "KO",
        "PEP",
    ]

    def __init__(self, store: DataStore | None = None):
        self.store = store or DataStore()
        self.settings = self.store.settings
        self.raw_universe_dir = self.settings.raw_data_dir / "us_equities"

    def build(self, fetch_remote: bool = False, min_count: int = 10000) -> pd.DataFrame:
        self.raw_universe_dir.mkdir(parents=True, exist_ok=True)
        if fetch_remote:
            self.fetch_source_files()

        frames = [
            self._load_nasdaq_listed(),
            self._load_other_listed(),
            self._load_sec_company_tickers(),
        ]
        frames = [frame for frame in frames if not frame.empty]

        if not frames:
            universe = self._seed_universe()
        else:
            universe = pd.concat(frames, ignore_index=True)

        universe = self._clean_universe(universe)
        universe = universe.head(min_count) if min_count else universe
        self.store.save_dataframe("processed", "us_equity_universe.csv", universe)
        self.store.save_json(
            "processed",
            "us_equity_universe_summary.json",
            {
                "ticker_count": int(len(universe)),
                "min_count_requested": int(min_count),
                "source_files_present": self._source_file_status(),
                "target_note": "Phase 1 target is at least 10K US tickers for broad universe coverage when source files allow it.",
            },
        )
        return universe

    def fetch_source_files(self) -> Dict[str, str]:
        headers = {"User-Agent": "financial-intelligence-engine research contact@example.com"}
        sources = {
            "nasdaqlisted.txt": NASDAQ_LISTED_URL,
            "otherlisted.txt": OTHER_LISTED_URL,
            "company_tickers.json": SEC_COMPANY_TICKERS_URL,
        }
        saved = {}
        for filename, url in sources.items():
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            path = self.raw_universe_dir / filename
            path.write_text(response.text, encoding="utf-8")
            saved[filename] = str(path)
        return saved

    def _load_nasdaq_listed(self) -> pd.DataFrame:
        path = self.raw_universe_dir / "nasdaqlisted.txt"
        if not path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(path, sep="|")
        frame = frame[frame["Symbol"].notna()]
        return pd.DataFrame(
            {
                "ticker": frame["Symbol"],
                "company_name": frame.get("Security Name", ""),
                "exchange": "NASDAQ",
                "source": "nasdaqtrader_nasdaqlisted",
            }
        )

    def _load_other_listed(self) -> pd.DataFrame:
        path = self.raw_universe_dir / "otherlisted.txt"
        if not path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(path, sep="|")
        frame = frame[frame["ACT Symbol"].notna()]
        return pd.DataFrame(
            {
                "ticker": frame["ACT Symbol"],
                "company_name": frame.get("Security Name", ""),
                "exchange": frame.get("Exchange", ""),
                "source": "nasdaqtrader_otherlisted",
            }
        )

    def _load_sec_company_tickers(self) -> pd.DataFrame:
        path = self.raw_universe_dir / "company_tickers.json"
        if not path.exists():
            return pd.DataFrame()
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.values() if isinstance(data, dict) else data
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        return pd.DataFrame(
            {
                "ticker": frame["ticker"],
                "company_name": frame.get("title", ""),
                "exchange": "SEC",
                "source": "sec_company_tickers",
            }
        )

    def _seed_universe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "ticker": self.SEED_TICKERS,
                "company_name": self.SEED_TICKERS,
                "exchange": "SEED",
                "source": "offline_seed",
            }
        )

    def _clean_universe(self, universe: pd.DataFrame) -> pd.DataFrame:
        universe = universe.copy()
        universe["ticker"] = universe["ticker"].astype(str).str.strip().str.upper()
        universe["company_name"] = universe["company_name"].astype(str).str.strip()
        universe["exchange"] = universe["exchange"].astype(str).str.strip()
        universe["source"] = universe["source"].astype(str).str.strip()

        invalid = {"", "NAN", "FILE CREATION TIME"}
        universe = universe[~universe["ticker"].isin(invalid)]
        universe = universe[~universe["ticker"].str.contains(r"\$", regex=True)]
        universe = universe.drop_duplicates(subset=["ticker"]).sort_values("ticker")
        return universe.reset_index(drop=True)

    def _source_file_status(self) -> List[Dict[str, str | bool]]:
        return [
            {"file": "nasdaqlisted.txt", "present": (self.raw_universe_dir / "nasdaqlisted.txt").exists()},
            {"file": "otherlisted.txt", "present": (self.raw_universe_dir / "otherlisted.txt").exists()},
            {"file": "company_tickers.json", "present": (self.raw_universe_dir / "company_tickers.json").exists()},
        ]


if __name__ == "__main__":
    settings = get_settings()
    store = DataStore(settings)
    store.initialize()
    universe = USEquityUniverseBuilder(store).build(fetch_remote=False)
    print(f"US equity universe cached with {len(universe)} tickers.")
