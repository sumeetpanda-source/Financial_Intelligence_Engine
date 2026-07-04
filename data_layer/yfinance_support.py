"""Shared yfinance runtime configuration."""

from __future__ import annotations

from pathlib import Path

import yfinance as yf

from config import get_settings


def configure_yfinance_cache() -> Path:
    """Point yfinance's SQLite caches at a known writable directory."""
    cache_dir = get_settings().data_root / "cache" / "yfinance"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(yf, "set_tz_cache_location"):
        yf.set_tz_cache_location(str(cache_dir))
    return cache_dir
