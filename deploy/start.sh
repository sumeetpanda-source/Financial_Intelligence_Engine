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

exec python -u frontend/server.py
