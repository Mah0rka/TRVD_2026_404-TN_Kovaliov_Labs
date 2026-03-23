from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.payment_service import PaymentService


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SubscriptionRepository(session)

    async def purchase(self, user_id: str, subscription_type: SubscriptionType) -> Subscription:
        existing_subscriptions = await self.repository.list_by_user(user_id)
        if any(
            subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.FROZEN}
            for subscription in existing_subscriptions
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Finish or pause your current membership before purchasing a new one",
            )

        if subscription_type == SubscriptionType.MONTHLY:
            duration_days = 30
            total_visits = 12
        elif subscription_type == SubscriptionType.YEARLY:
            duration_days = 365
            total_visits = None
        elif subscription_type == SubscriptionType.PAY_AS_YOU_GO:
            duration_days = 30
            total_visits = 1
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription type")

        start_date = datetime.now(UTC)
        end_date = start_date + timedelta(days=duration_days)
        payment_service = PaymentService(self.repository.session)

        subscription = Subscription(
            user_id=user_id,
            type=subscription_type,
            start_date=start_date,
            end_date=end_date,
            total_visits=total_visits,
            remaining_visits=total_visits,
            status=SubscriptionStatus.ACTIVE,
        )
        payment = payment_service.build_subscription_payment(user_id, subscription_type)

        self.repository.session.add_all([subscription, payment])
        await self.repository.session.commit()
        await self.repository.session.refresh(subscription)
        return subscription

    async def freeze(self, user_id: str, subscription_id: str, days: int) -> Subscription:
        subscription = await self.repository.get_by_id(subscription_id)
        if not subscription or subscription.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active subscriptions can be frozen")

        subscription.status = SubscriptionStatus.FROZEN
        subscription.end_date = subscription.end_date + timedelta(days=days)
        await self.repository.session.commit()
        await self.repository.session.refresh(subscription)
        return subscription

    async def list_for_user(self, user_id: str) -> list[Subscription]:
        return await self.repository.list_by_user(user_id)
