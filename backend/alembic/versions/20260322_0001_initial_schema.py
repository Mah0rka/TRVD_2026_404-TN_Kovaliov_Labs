# Коротко: міграція фіксує зміну схеми для модуля 20260322 0001 initial schema.

"""Initial schema

Revision ID: 20260322_0001
Revises:
Create Date: 2026-03-22 21:30:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260322_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("CLIENT", "TRAINER", "ADMIN", "OWNER", name="user_role", create_type=False)
subscription_type = postgresql.ENUM(
    "MONTHLY", "YEARLY", "PAY_AS_YOU_GO", name="subscription_type", create_type=False
)
subscription_status = postgresql.ENUM(
    "ACTIVE", "FROZEN", "EXPIRED", name="subscription_status", create_type=False
)
workout_type = postgresql.ENUM("GROUP", "PERSONAL", name="workout_type", create_type=False)
booking_status = postgresql.ENUM("CONFIRMED", "CANCELLED", name="booking_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    subscription_type.create(bind, checkfirst=True)
    subscription_status.create(bind, checkfirst=True)
    workout_type.create(bind, checkfirst=True)
    booking_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="CLIENT"),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workout_classes",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trainer_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("type", workout_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workout_classes_start_time", "workout_classes", ["start_time"], unique=False)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", subscription_type, nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", subscription_status, nullable=False, server_default="ACTIVE"),
        sa.Column("total_visits", sa.Integer(), nullable=True),
        sa.Column("remaining_visits", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"], unique=False)
    op.create_index("ix_subscriptions_end_date", "subscriptions", ["end_date"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="UAH"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_created_at", "payments", ["created_at"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.String(length=36), sa.ForeignKey("workout_classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", booking_status, nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "class_id", name="uq_bookings_user_class"),
    )
    op.create_index("ix_bookings_user_class", "bookings", ["user_id", "class_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_bookings_user_class", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("ix_payments_created_at", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_subscriptions_end_date", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_workout_classes_start_time", table_name="workout_classes")
    op.drop_table("workout_classes")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    booking_status.drop(bind, checkfirst=True)
    workout_type.drop(bind, checkfirst=True)
    subscription_status.drop(bind, checkfirst=True)
    subscription_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
