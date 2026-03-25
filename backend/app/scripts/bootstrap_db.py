# Коротко: скрипт підтримує службові операції для модуля ініціалізації бази даних.

import asyncio
import logging
import subprocess
import sys

from sqlalchemy import inspect

from app.core.database import engine

logger = logging.getLogger(__name__)

APP_TABLES = {"users", "workout_classes", "subscriptions", "payments", "bookings", "membership_plans"}


async def ensure_migrations_applied() -> None:
    async with engine.begin() as connection:
        table_names = set(await connection.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names()))

    if "alembic_version" not in table_names and APP_TABLES.intersection(table_names):
        logger.info("Existing schema detected without alembic metadata, stamping head")
        _run_alembic_command("stamp", "head")
        return

    logger.info("Running alembic upgrade head")
    _run_alembic_command("upgrade", "head")


def _run_alembic_command(*args: str) -> None:
    result = subprocess.run(["alembic", *args], check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    asyncio.run(ensure_migrations_applied())


if __name__ == "__main__":
    main()
