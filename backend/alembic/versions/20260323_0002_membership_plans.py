# Коротко: міграція фіксує зміну схеми для модуля 20260323 0002 membership plans.

"""Add membership plans

Revision ID: 20260323_0002
Revises: 20260322_0001
Create Date: 2026-03-23 23:59:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260323_0002"
down_revision = "20260322_0001"
branch_labels = None
depends_on = None


subscription_type = postgresql.ENUM(
    "MONTHLY", "YEARLY", "PAY_AS_YOU_GO", name="subscription_type", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    subscription_type.create(bind, checkfirst=True)

    op.create_table(
        "membership_plans",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", subscription_type, nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("visits_limit", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="UAH"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_membership_plans_is_active", "membership_plans", ["is_active"], unique=False)
    op.create_index("ix_membership_plans_sort_order", "membership_plans", ["sort_order"], unique=False)

    op.add_column("subscriptions", sa.Column("plan_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_subscriptions_plan_id_membership_plans",
        "subscriptions",
        "membership_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_plan_id_membership_plans", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "plan_id")
    op.drop_index("ix_membership_plans_sort_order", table_name="membership_plans")
    op.drop_index("ix_membership_plans_is_active", table_name="membership_plans")
    op.drop_table("membership_plans")
