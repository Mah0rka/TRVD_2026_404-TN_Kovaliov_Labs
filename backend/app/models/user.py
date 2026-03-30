# Модель описує структуру доменних сутностей і звʼязків між ними.

import enum
import uuid

from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    TRAINER = "TRAINER"
    ADMIN = "ADMIN"
    OWNER = "OWNER"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.CLIENT)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Subscription.user_id",
    )
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    classes = relationship(
        "WorkoutClass",
        back_populates="trainer",
        cascade="all, delete-orphan",
        foreign_keys="WorkoutClass.trainer_id",
    )
    class_series = relationship(
        "WorkoutSeries",
        back_populates="trainer",
        cascade="all, delete-orphan",
        foreign_keys="WorkoutSeries.trainer_id",
    )
    subscription_edits = relationship(
        "Subscription",
        foreign_keys="Subscription.last_modified_by_id",
        back_populates="last_modified_by",
    )
    subscription_deletions = relationship(
        "Subscription",
        foreign_keys="Subscription.deleted_by_id",
        back_populates="deleted_by",
    )
    subscription_restorations = relationship(
        "Subscription",
        foreign_keys="Subscription.restored_by_id",
        back_populates="restored_by",
    )
