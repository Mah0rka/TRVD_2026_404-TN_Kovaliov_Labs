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

    async def get_by_id(self, subscription_id: str, include_deleted: bool = False) -> Subscription | None:
        statement = (
            select(Subscription)
            .execution_options(populate_existing=True)
            .where(Subscription.id == subscription_id)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
                selectinload(Subscription.last_modified_by),
                selectinload(Subscription.deleted_by),
                selectinload(Subscription.restored_by),
            )
        )
        if not include_deleted:
            statement = statement.where(Subscription.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: str, include_deleted: bool = False) -> list[Subscription]:
        statement = (
            select(Subscription)
            .execution_options(populate_existing=True)
            .where(Subscription.user_id == user_id)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
                selectinload(Subscription.last_modified_by),
                selectinload(Subscription.deleted_by),
                selectinload(Subscription.restored_by),
            )
            .order_by(Subscription.end_date.desc())
        )
        if not include_deleted:
            statement = statement.where(Subscription.deleted_at.is_(None))
        result = await self.session.execute(
            statement
        )
        return list(result.scalars().all())

    async def list_by_plan(self, plan_id: str) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(Subscription.plan_id == plan_id, Subscription.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        user_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[Subscription]:
        statement = (
            select(Subscription)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
                selectinload(Subscription.last_modified_by),
                selectinload(Subscription.deleted_by),
                selectinload(Subscription.restored_by),
            )
            .order_by(Subscription.created_at.desc())
        )
        if user_id:
            statement = statement.where(Subscription.user_id == user_id)
        if not include_deleted:
            statement = statement.where(Subscription.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_active_by_user(self, user_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.deleted_at.is_(None),
            )
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
                selectinload(Subscription.last_modified_by),
                selectinload(Subscription.deleted_by),
                selectinload(Subscription.restored_by),
            )
            .order_by(Subscription.end_date.desc())
        )
        return result.scalars().first()

    async def list_expired_candidates(self, now: datetime) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date < now,
                Subscription.deleted_at.is_(None),
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
                Subscription.deleted_at.is_(None),
            )
            .options(selectinload(Subscription.user), selectinload(Subscription.plan))
        )
        return list(result.scalars().all())
