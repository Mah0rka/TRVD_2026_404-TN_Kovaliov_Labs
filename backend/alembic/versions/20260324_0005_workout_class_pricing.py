# Коротко: міграція фіксує зміну схеми для модуля 20260324 0005 workout class pricing.

"""workout class pricing and booking rules support

Revision ID: 20260324_0005
Revises: 20260324_0004
Create Date: 2026-03-24 23:15:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_0005"
down_revision: str | None = "20260324_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workout_classes",
        sa.Column("is_paid_extra", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "workout_classes",
        sa.Column("extra_price", sa.Numeric(12, 2), nullable=True),
    )
    op.alter_column("workout_classes", "is_paid_extra", server_default=None)


def downgrade() -> None:
    op.drop_column("workout_classes", "extra_price")
    op.drop_column("workout_classes", "is_paid_extra")
