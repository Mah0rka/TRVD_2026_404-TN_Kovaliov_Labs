# Модуль описує фонові задачі та їх точки входу.

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.services.notification_service import NotificationService
from app.services.schedule_service import ScheduleService

TaskResult = TypeVar("TaskResult")

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
        "materialize-schedule-series": {
            "task": "fcms.schedules.materialize_future_occurrences",
            "schedule": 60 * 60 * 24,
        },
    },
)


# Повертає просту відповідь для перевірки доступності worker-команди.
@celery_app.task(name="fcms.debug.ping")
def ping() -> str:
    return "pong"


# Створює окремий engine/session factory для Celery-задач без повторного використання pool між loop-ами.
def _create_task_session_factory() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return engine, session_factory


# Виконує DB-операцію в ізольованому async engine та гарантовано dispose-ить його до закриття loop.
async def _run_with_isolated_session(
    operation: Callable[[AsyncSession], Awaitable[TaskResult]],
) -> TaskResult:
    engine, session_factory = _create_task_session_factory()
    try:
        async with session_factory() as session:
            return await operation(session)
    finally:
        await engine.dispose()


# Запускає асинхронний сценарій завершення прострочених абонементів.
async def _run_expire_subscriptions() -> int:
    async def operation(session: AsyncSession) -> int:
        service = NotificationService(session)
        return await service.expire_subscriptions()

    return await _run_with_isolated_session(operation)


# Запускає асинхронний сценарій збору нагадувань по абонементах.
async def _run_subscription_reminders() -> list[dict[str, str]]:
    async def operation(session: AsyncSession) -> list[dict[str, str]]:
        service = NotificationService(session)
        return await service.collect_expiration_reminders()

    return await _run_with_isolated_session(operation)


# Добудовує materialized occurrences recurring-серій у межах горизонту планування.
async def _run_materialize_future_occurrences() -> int:
    async def operation(session: AsyncSession) -> int:
        service = ScheduleService(session)
        return await service.materialize_future_occurrences()

    return await _run_with_isolated_session(operation)


# Викликає фонове завершення прострочених абонементів.
@celery_app.task(name="fcms.notifications.expire_subscriptions")
def expire_subscriptions() -> int:
    return asyncio.run(_run_expire_subscriptions())


# Запускає фоновий збір нагадувань про завершення абонементів.
@celery_app.task(name="fcms.notifications.subscription_reminders")
def subscription_reminders() -> list[dict[str, str]]:
    return asyncio.run(_run_subscription_reminders())


# Запускає nightly materialization для recurring-серій занять.
@celery_app.task(name="fcms.schedules.materialize_future_occurrences")
def materialize_future_occurrences() -> int:
    return asyncio.run(_run_materialize_future_occurrences())
