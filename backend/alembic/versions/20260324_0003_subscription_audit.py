# Коротко: міграція фіксує зміну схеми для модуля абонементів.

"""Add subscription audit fields

Revision ID: 20260324_0003
Revises: 20260323_0002
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260324_0003"
down_revision = "20260323_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("last_modified_by_id", sa.String(length=36), nullable=True))
    op.add_column("subscriptions", sa.Column("last_modified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("deleted_by_id", sa.String(length=36), nullable=True))
    op.add_column("subscriptions", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key(
        "fk_subscriptions_last_modified_by_id_users",
        "subscriptions",
        "users",
        ["last_modified_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_subscriptions_deleted_by_id_users",
        "subscriptions",
        "users",
        ["deleted_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_subscriptions_deleted_at", "subscriptions", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_subscriptions_deleted_at", table_name="subscriptions")
    op.drop_constraint("fk_subscriptions_deleted_by_id_users", "subscriptions", type_="foreignkey")
    op.drop_constraint("fk_subscriptions_last_modified_by_id_users", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "deleted_at")
    op.drop_column("subscriptions", "deleted_by_id")
    op.drop_column("subscriptions", "last_modified_at")
    op.drop_column("subscriptions", "last_modified_by_id")
