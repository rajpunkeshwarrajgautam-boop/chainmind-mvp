#!/usr/bin/env bash
# Run the API locally without Docker (SQLite + in-process Celery).
# Usage: ./scripts/run_local.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export ENVIRONMENT="${ENVIRONMENT:-development}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./chainmind-local.db}"
export JWT_SECRET="${JWT_SECRET:-local-dev-jwt-secret-minimum-32-characters}"
export CELERY_TASK_ALWAYS_EAGER="${CELERY_TASK_ALWAYS_EAGER:-true}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
echo "Starting ChainMind at http://127.0.0.1:8000/docs (Ctrl+C to stop)"
exec python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
