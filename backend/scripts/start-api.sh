#!/bin/sh
set -e

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  python -m app.scripts.bootstrap_db
fi

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m app.scripts.seed_demo
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
