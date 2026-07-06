#!/bin/sh
set -eu

DATA_ROOT="${FIE_DATA_ROOT:-/var/data}"
MODEL_ROOT="${FIE_MODEL_DIR:-${DATA_ROOT}/models}"
REPORTS_ROOT="${FIE_REPORTS_DIR:-${DATA_ROOT}/reports}"

mkdir -p "${DATA_ROOT}" "${MODEL_ROOT}" "${REPORTS_ROOT}"

# Seed only missing files so a persistent disk keeps later indexes and outputs.
cp -a -n /app/bootstrap_data/. "${DATA_ROOT}/"
cp -a -n /app/bootstrap_models/. "${MODEL_ROOT}/"
cp -a -n /app/bootstrap_reports/. "${REPORTS_ROOT}/"

# When an SEC identity is configured, add a small official filing corpus to RAG.
if [ -n "${FIE_SEC_USER_AGENT:-}" ] && [ ! -f "${DATA_ROOT}/raw/sec_filings/ingestion_manifest.json" ]; then
    python ingest_sec_filings.py --tickers AAPL MSFT NVDA --forms 10-K 10-Q --per-form 1 \
        || echo "SEC filing bootstrap failed; continuing with the packaged RAG corpus."
fi

exec python -u frontend/server.py
