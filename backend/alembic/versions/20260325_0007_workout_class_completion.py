# Коротко: міграція додає підтвердження завершення заняття та коментар.

"""workout class completion metadata

Revision ID: 20260325_0007
Revises: 20260324_0006
Create Date: 2026-03-25 22:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260325_0007"
down_revision: str | None = "20260324_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout_classes", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workout_classes", sa.Column("completion_comment", sa.Text(), nullable=True))
    op.add_column("workout_classes", sa.Column("completed_by_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_workout_classes_completed_by_id_users",
        "workout_classes",
        "users",
        ["completed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_workout_classes_completed_by_id_users", "workout_classes", type_="foreignkey")
    op.drop_column("workout_classes", "completed_by_id")
    op.drop_column("workout_classes", "completion_comment")
    op.drop_column("workout_classes", "completed_at")
