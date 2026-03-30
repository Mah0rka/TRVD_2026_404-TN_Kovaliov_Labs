# Коротко: додає recurring-серії занять та звʼязок із materialized occurrences.

"""schedule recurring series

Revision ID: 20260328_0008
Revises: 20260325_0007
Create Date: 2026-03-28 19:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260328_0008"
down_revision: str | None = "20260325_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    recurrence_frequency = postgresql.ENUM(
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        name="recurrence_frequency",
        create_type=False,
    )
    workout_type = postgresql.ENUM("GROUP", "PERSONAL", name="workout_type", create_type=False)
    recurrence_frequency.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "workout_series",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trainer_id", sa.String(length=36), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("type", workout_type, nullable=False),
        sa.Column("is_paid_extra", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("extra_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("frequency", recurrence_frequency, nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("by_weekday", sa.String(length=32), nullable=True),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.Column("until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Kiev"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_series_trainer_start", "workout_series", ["trainer_id", "start_time"])
    op.create_index("ix_workout_series_until", "workout_series", ["until"])

    op.create_table(
        "workout_series_exclusions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("series_id", sa.String(length=36), nullable=False),
        sa.Column("occurrence_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["series_id"], ["workout_series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("series_id", "occurrence_start", name="uq_series_exclusions_series_occurrence"),
    )
    op.create_index(
        "ix_series_exclusions_occurrence_start",
        "workout_series_exclusions",
        ["occurrence_start"],
    )

    op.add_column("workout_classes", sa.Column("series_id", sa.String(length=36), nullable=True))
    op.add_column("workout_classes", sa.Column("source_occurrence_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "workout_classes",
        sa.Column("is_series_exception", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_foreign_key(
        "fk_workout_classes_series_id_workout_series",
        "workout_classes",
        "workout_series",
        ["series_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_workout_classes_series_id", "workout_classes", ["series_id"])
    op.create_unique_constraint(
        "uq_workout_class_series_occurrence",
        "workout_classes",
        ["series_id", "source_occurrence_start"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_workout_class_series_occurrence", "workout_classes", type_="unique")
    op.drop_index("ix_workout_classes_series_id", table_name="workout_classes")
    op.drop_constraint("fk_workout_classes_series_id_workout_series", "workout_classes", type_="foreignkey")
    op.drop_column("workout_classes", "is_series_exception")
    op.drop_column("workout_classes", "source_occurrence_start")
    op.drop_column("workout_classes", "series_id")

    op.drop_index("ix_series_exclusions_occurrence_start", table_name="workout_series_exclusions")
    op.drop_table("workout_series_exclusions")

    op.drop_index("ix_workout_series_until", table_name="workout_series")
    op.drop_index("ix_workout_series_trainer_start", table_name="workout_series")
    op.drop_table("workout_series")

    recurrence_frequency = postgresql.ENUM(
        "DAILY",
        "WEEKLY",
        "MONTHLY",
        name="recurrence_frequency",
        create_type=False,
    )
    recurrence_frequency.drop(op.get_bind(), checkfirst=True)
