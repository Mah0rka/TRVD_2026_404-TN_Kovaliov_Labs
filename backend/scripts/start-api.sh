#!/bin/sh
# Starts the backend API process.

set -e

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  python -m app.scripts.bootstrap_db
fi

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m app.scripts.seed_demo
fi

UVICORN_HOST="${UVICORN_HOST:-0.0.0.0}"
UVICORN_PORT="${UVICORN_PORT:-8000}"
UVICORN_RELOAD="${UVICORN_RELOAD:-false}"
UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

if [ "$UVICORN_RELOAD" = "true" ]; then
  exec uvicorn app.main:app --host "$UVICORN_HOST" --port "$UVICORN_PORT" --reload
fi

exec uvicorn app.main:app --host "$UVICORN_HOST" --port "$UVICORN_PORT" --workers "$UVICORN_WORKERS"
