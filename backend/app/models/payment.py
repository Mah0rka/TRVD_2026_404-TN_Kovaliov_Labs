# Модель описує структуру доменних сутностей і звʼязків між ними.

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


"""Модель зберігає транзакції за абонементи та додаткові послуги клубу."""


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="UAH")
    status: Mapped[str] = mapped_column(String(32))
    method: Mapped[str] = mapped_column(String(32))
    purpose: Mapped[str] = mapped_column(String(32), default="GENERAL")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    booking_class_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    user = relationship("User", back_populates="payments")
