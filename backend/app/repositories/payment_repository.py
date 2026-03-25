# Коротко: репозиторій інкапсулює доступ до даних для модуля платежів.

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_by_id(self, payment_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id).options(selectinload(Payment.user))
        )
        return result.scalar_one_or_none()

    async def get_pending_booking_payment(self, user_id: str, class_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.booking_class_id == class_id,
                Payment.purpose == "BOOKING_EXTRA",
                Payment.status == "PENDING",
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.purpose == "SUBSCRIPTION",
            )
            .options(selectinload(Payment.user))
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        user_id: str | None = None,
        status: str | None = None,
        method: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Payment]:
        statement = select(Payment).options(selectinload(Payment.user)).order_by(Payment.created_at.desc())
        if user_id:
            statement = statement.where(Payment.user_id == user_id)
        if status:
            statement = statement.where(Payment.status == status.upper())
        if method:
            statement = statement.where(Payment.method == method.upper())
        if start_date:
            statement = statement.where(Payment.created_at >= start_date)
        if end_date:
            statement = statement.where(Payment.created_at <= end_date)

        result = await self.session.execute(statement)
        return list(result.scalars().all())
