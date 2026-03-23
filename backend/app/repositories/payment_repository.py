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

    async def list_by_user(self, user_id: str) -> list[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
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
