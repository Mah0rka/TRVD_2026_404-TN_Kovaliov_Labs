# Тести перевіряють ключові сценарії цього модуля.

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.subscription import SubscriptionStatus
from app.services.notification_service import NotificationService


# Перевіряє, що expire subscriptions updates status and commits працює коректно.
@pytest.mark.asyncio
async def test_expire_subscriptions_updates_status_and_commits():
    session = AsyncMock()
    service = NotificationService(session)

    expiring = [
        SimpleNamespace(id="sub-1", status=SubscriptionStatus.ACTIVE),
        SimpleNamespace(id="sub-2", status=SubscriptionStatus.ACTIVE),
    ]
    service.repository = SimpleNamespace(list_expired_candidates=AsyncMock(return_value=expiring))

    updated_count = await service.expire_subscriptions()

    assert updated_count == 2
    assert all(subscription.status == SubscriptionStatus.EXPIRED for subscription in expiring)
    session.commit.assert_awaited_once()


# Перевіряє, що collect expiration reminders returns payloads працює коректно.
@pytest.mark.asyncio
async def test_collect_expiration_reminders_returns_payloads():
    session = AsyncMock()
    service = NotificationService(session)

    subscription = SimpleNamespace(
        id="sub-1",
        end_date=datetime.now(UTC) + timedelta(days=3),
        user=SimpleNamespace(email="client@example.com"),
    )
    service.repository = SimpleNamespace(list_expiring_between=AsyncMock(return_value=[subscription]))
    service.redis = SimpleNamespace(set=AsyncMock(return_value=True))

    reminders = await service.collect_expiration_reminders()

    assert reminders == [
        {
            "subscription_id": "sub-1",
            "email": "client@example.com",
            "end_date": subscription.end_date.isoformat(),
        }
    ]
