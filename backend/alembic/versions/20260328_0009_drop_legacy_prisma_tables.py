"""Drop legacy Prisma tables

Revision ID: 20260328_0009
Revises: 20260328_0008
Create Date: 2026-03-28 19:25:00
"""

import sqlalchemy as sa
from alembic import op


revision = "20260328_0009"
down_revision = "20260328_0008"
branch_labels = None
depends_on = None


LEGACY_TABLES = (
    "_prisma_migrations",
    "Booking",
    "Payment",
    "Subscription",
    "User",
    "WorkoutClass",
)


def upgrade() -> None:
    for table_name in LEGACY_TABLES:
        quoted_name = table_name.replace('"', '""')
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{quoted_name}" CASCADE'))


def downgrade() -> None:
    # Дані цих таблиць не використовуються поточним застосунком.
    # Під час rollback legacy-артефакти не відновлюються автоматично.
    pass
