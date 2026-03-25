# Сервіс інкапсулює бізнес-правила та координує роботу репозиторіїв.

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.subscription import Subscription, SubscriptionStatus
from app.repositories.subscription_repository import SubscriptionRepository

logger = logging.getLogger(__name__)


class NotificationService:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SubscriptionRepository(session)
        self.redis = get_redis()

    # Викликає фонове завершення прострочених абонементів.
    async def expire_subscriptions(self) -> int:
        now = datetime.now(UTC)
        subscriptions = await self.repository.list_expired_candidates(now)

        for subscription in subscriptions:
            subscription.status = SubscriptionStatus.EXPIRED

        if subscriptions:
            await self.session.commit()

        logger.info("notification_job=expire_subscriptions expired_count=%s", len(subscriptions))
        return len(subscriptions)

    # Збирає expiration reminders.
    async def collect_expiration_reminders(self, days_ahead: int = 3) -> list[dict[str, str]]:
        start = datetime.now(UTC) + timedelta(days=days_ahead - 1)
        end = datetime.now(UTC) + timedelta(days=days_ahead)
        subscriptions = await self.repository.list_expiring_between(start, end)

        reminders: list[dict[str, str]] = []
        for subscription in subscriptions:
            reminder = self._build_reminder_payload(subscription)
            if await self._should_emit_reminder(reminder):
                reminders.append(reminder)

        for reminder in reminders:
            logger.info(
                "notification_job=subscription_reminders channel=email email=%s subscription_id=%s",
                reminder["email"],
                reminder["subscription_id"],
            )

        return reminders

    # Формує reminder payload.
    def _build_reminder_payload(self, subscription: Subscription) -> dict[str, str]:
        return {
            "subscription_id": subscription.id,
            "email": subscription.user.email,
            "end_date": subscription.end_date.isoformat(),
        }

    # Виконує внутрішній крок для сценарію should emit reminder.
    async def _should_emit_reminder(self, reminder: dict[str, str]) -> bool:
        reminder_key = (
            f"notifications:subscription-expiring:{reminder['subscription_id']}:{reminder['end_date'][:10]}"
        )
        created = await self.redis.set(reminder_key, "1", ex=60 * 60 * 24 * 7, nx=True)
        return bool(created)
