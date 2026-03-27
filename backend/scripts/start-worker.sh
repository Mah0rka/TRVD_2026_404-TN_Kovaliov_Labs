#!/bin/sh
# Starts the Celery worker process.

set -e

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  python -m app.scripts.bootstrap_db
fi

exec celery -A app.tasks.celery_app.celery_app worker --loglevel=info
