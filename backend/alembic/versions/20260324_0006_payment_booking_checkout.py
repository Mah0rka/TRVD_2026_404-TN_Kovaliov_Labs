"""payment booking checkout metadata

Revision ID: 20260324_0006
Revises: 20260324_0005
Create Date: 2026-03-24 23:45:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_0006"
down_revision: str | None = "20260324_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("purpose", sa.String(length=32), nullable=False, server_default="SUBSCRIPTION"))
    op.add_column("payments", sa.Column("description", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("booking_class_id", sa.String(length=36), nullable=True))
    op.alter_column("payments", "purpose", server_default=None)


def downgrade() -> None:
    op.drop_column("payments", "booking_class_id")
    op.drop_column("payments", "description")
    op.drop_column("payments", "purpose")
