"""Tests for the frontend server's cloud readiness helpers."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from frontend.server import build_health


def test_health_reports_service_and_artifact_checks():
    health = build_health()

    assert health["service"] == "financial-intelligence-engine"
    assert health["status"] in {"ok", "degraded"}
    assert set(health["checks"]) == {
        "universe",
        "features",
        "risk_model",
        "forecast_model",
        "vector_store",
    }
