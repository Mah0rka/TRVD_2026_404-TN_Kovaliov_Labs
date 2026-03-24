import enum
import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WorkoutType(str, enum.Enum):
    GROUP = "GROUP"
    PERSONAL = "PERSONAL"


class WorkoutClass(Base, TimestampMixin):
    __tablename__ = "workout_classes"
    __table_args__ = (Index("ix_workout_classes_start_time", "start_time"),)

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

    trainer = relationship("User", back_populates="classes")
    bookings = relationship("Booking", back_populates="workout_class", cascade="all, delete-orphan")
