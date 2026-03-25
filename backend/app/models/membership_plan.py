# Модель описує структуру доменних сутностей і звʼязків між ними.

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.subscription import SubscriptionType


class MembershipPlan(Base, TimestampMixin):
    __tablename__ = "membership_plans"
    __table_args__ = (
        Index("ix_membership_plans_is_active", "is_active"),
        Index("ix_membership_plans_is_public", "is_public"),
        Index("ix_membership_plans_sort_order", "sort_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    type: Mapped[SubscriptionType] = mapped_column(Enum(SubscriptionType, name="subscription_type"))
    duration_days: Mapped[int]
    visits_limit: Mapped[int | None]
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="UAH")
    sort_order: Mapped[int] = mapped_column(default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="plan")
