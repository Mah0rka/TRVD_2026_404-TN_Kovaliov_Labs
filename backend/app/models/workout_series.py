# Модель описує recurring-серії занять і їх винятки.

import enum
import uuid

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.workout_class import WorkoutType


# Перелічує підтримувані типи повторення recurring-серій.
class RecurrenceFrequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


# Зберігає шаблон recurring-серії, з якого materialize-яться окремі заняття.
class WorkoutSeries(Base, TimestampMixin):
    __tablename__ = "workout_series"
    __table_args__ = (
        Index("ix_workout_series_trainer_start", "trainer_id", "start_time"),
        Index("ix_workout_series_until", "until"),
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
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency, name="recurrence_frequency")
    )
    interval: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    by_weekday: Mapped[str | None] = mapped_column(String(32), nullable=True)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rule_text: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Kiev", server_default="Europe/Kiev")

    trainer = relationship("User", back_populates="class_series")
    occurrences = relationship("WorkoutClass", back_populates="series")
    exclusions = relationship(
        "WorkoutSeriesExclusion",
        back_populates="series",
        cascade="all, delete-orphan",
    )


# Фіксує окремі дати, які треба пропустити в recurring-серії.
class WorkoutSeriesExclusion(Base, TimestampMixin):
    __tablename__ = "workout_series_exclusions"
    __table_args__ = (
        UniqueConstraint("series_id", "occurrence_start", name="uq_series_exclusions_series_occurrence"),
        Index("ix_series_exclusions_occurrence_start", "occurrence_start"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    series_id: Mapped[str] = mapped_column(ForeignKey("workout_series.id", ondelete="CASCADE"))
    occurrence_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    series = relationship("WorkoutSeries", back_populates="exclusions")
