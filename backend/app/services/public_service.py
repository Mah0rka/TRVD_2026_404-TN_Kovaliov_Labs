from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass
from app.schemas.public import ClubStats


class PublicService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def club_stats(self) -> ClubStats:
        now = datetime.now(UTC)
        week_ahead = now + timedelta(days=7)

        clients_result = await self.session.execute(
            select(func.count(User.id)).where(User.role == UserRole.CLIENT)
        )
        trainers_result = await self.session.execute(
            select(func.count(User.id)).where(User.role == UserRole.TRAINER)
        )
        classes_result = await self.session.execute(
            select(func.count(WorkoutClass.id)).where(
                WorkoutClass.start_time >= now,
                WorkoutClass.start_time <= week_ahead,
            )
        )
        subscriptions_result = await self.session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )

        return ClubStats(
            clients_count=int(clients_result.scalar_one() or 0),
            trainers_count=int(trainers_result.scalar_one() or 0),
            classes_next_7_days=int(classes_result.scalar_one() or 0),
            active_subscriptions_count=int(subscriptions_result.scalar_one() or 0),
        )
