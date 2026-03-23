from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, subscription: Subscription) -> Subscription:
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def get_by_id(self, subscription_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.end_date.desc())
        )
        return list(result.scalars().all())

    async def get_active_by_user(self, user_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .order_by(Subscription.end_date.desc())
        )
        return result.scalars().first()

    async def list_expired_candidates(self, now: datetime) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date < now,
            )
        )
        return list(result.scalars().all())

    async def list_expiring_between(self, start: datetime, end: datetime) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date >= start,
                Subscription.end_date <= end,
            )
            .options(selectinload(Subscription.user))
        )
        return list(result.scalars().all())
