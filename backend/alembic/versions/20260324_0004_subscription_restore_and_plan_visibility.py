# Коротко: міграція фіксує зміну схеми для модуля абонементів.

"""subscription restore audit and plan visibility

Revision ID: 20260324_0004
Revises: 20260324_0003
Create Date: 2026-03-24 22:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_0004"
down_revision: str | None = "20260324_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("membership_plans", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_membership_plans_is_public", "membership_plans", ["is_public"], unique=False)
    op.alter_column("membership_plans", "is_public", server_default=None)

    op.add_column("subscriptions", sa.Column("restored_by_id", sa.String(length=36), nullable=True))
    op.add_column("subscriptions", sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_subscriptions_restored_by_id_users",
        "subscriptions",
        "users",
        ["restored_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_restored_by_id_users", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "restored_at")
    op.drop_column("subscriptions", "restored_by_id")

    op.drop_index("ix_membership_plans_is_public", table_name="membership_plans")
    op.drop_column("membership_plans", "is_public")
