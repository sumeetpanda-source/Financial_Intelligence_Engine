"""Tests for writable yfinance cache configuration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_layer.yfinance_support import configure_yfinance_cache


def test_yfinance_cache_uses_configured_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("FIE_DATA_ROOT", str(tmp_path))

    cache_dir = configure_yfinance_cache()

    assert cache_dir == tmp_path / "cache" / "yfinance"
    assert cache_dir.is_dir()
