# Модель описує структуру доменних сутностей і звʼязків між ними.

import enum
import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WorkoutType(str, enum.Enum):
    GROUP = "GROUP"
    PERSONAL = "PERSONAL"


class WorkoutClass(Base, TimestampMixin):
    __tablename__ = "workout_classes"
    __table_args__ = (
        Index("ix_workout_classes_start_time", "start_time"),
        Index("ix_workout_classes_series_id", "series_id"),
        UniqueConstraint("series_id", "source_occurrence_start", name="uq_workout_class_series_occurrence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trainer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    type: Mapped[WorkoutType] = mapped_column(Enum(WorkoutType, name="workout_type"))
    is_paid_extra: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    extra_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    series_id: Mapped[str | None] = mapped_column(
        ForeignKey("workout_series.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_occurrence_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_series_exception: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    trainer = relationship("User", back_populates="classes", foreign_keys=[trainer_id])
    bookings = relationship("Booking", back_populates="workout_class", cascade="all, delete-orphan")
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    series = relationship("WorkoutSeries", back_populates="occurrences")

    @property
    def recurrence(self):
        if not self.series:
            return None
        from app.services.schedule_recurrence import recurrence_to_read

        return recurrence_to_read(self.series)
