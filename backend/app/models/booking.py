import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "class_id", name="uq_bookings_user_class"),
        Index("ix_bookings_user_class", "user_id", "class_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    class_id: Mapped[str] = mapped_column(ForeignKey("workout_classes.id", ondelete="CASCADE"))
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.CONFIRMED,
    )

    user = relationship("User", back_populates="bookings")
    workout_class = relationship("WorkoutClass", back_populates="bookings")
