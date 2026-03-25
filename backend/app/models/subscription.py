# Модель описує структуру доменних сутностей і звʼязків між ними.

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SubscriptionType(str, enum.Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    PAY_AS_YOU_GO = "PAY_AS_YOU_GO"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    EXPIRED = "EXPIRED"


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_end_date", "end_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[SubscriptionType] = mapped_column(Enum(SubscriptionType, name="subscription_type"))
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.ACTIVE,
    )
    total_visits: Mapped[int | None]
    remaining_visits: Mapped[int | None]
    last_modified_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    restored_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscriptions", foreign_keys=[user_id])
    plan = relationship("MembershipPlan", back_populates="subscriptions")
    last_modified_by = relationship("User", foreign_keys=[last_modified_by_id], back_populates="subscription_edits")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id], back_populates="subscription_deletions")
    restored_by = relationship("User", foreign_keys=[restored_by_id], back_populates="subscription_restorations")
