import asyncio

from celery import Celery

from app.core.database import async_session_factory
from app.services.notification_service import NotificationService

from app.core.config import settings

celery_app = Celery(
    "fcms",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "expire-subscriptions-nightly": {
            "task": "fcms.notifications.expire_subscriptions",
            "schedule": 60 * 60 * 24,
        },
        "send-subscription-reminders": {
            "task": "fcms.notifications.subscription_reminders",
            "schedule": 60 * 60 * 24,
        },
    },
)


@celery_app.task(name="fcms.debug.ping")
def ping() -> str:
    return "pong"


async def _run_expire_subscriptions() -> int:
    async with async_session_factory() as session:
        service = NotificationService(session)
        return await service.expire_subscriptions()


async def _run_subscription_reminders() -> list[dict[str, str]]:
    async with async_session_factory() as session:
        service = NotificationService(session)
        return await service.collect_expiration_reminders()


@celery_app.task(name="fcms.notifications.expire_subscriptions")
def expire_subscriptions() -> int:
    return asyncio.run(_run_expire_subscriptions())


@celery_app.task(name="fcms.notifications.subscription_reminders")
def subscription_reminders() -> list[dict[str, str]]:
    return asyncio.run(_run_subscription_reminders())
