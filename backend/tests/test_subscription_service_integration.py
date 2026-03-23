from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.services.subscription_service import SubscriptionService


@pytest.mark.asyncio
async def test_freeze_subscription_extends_end_date_and_sets_status(db_session):
    client = User(
        email="freeze-client@example.com",
        password_hash="hash",
        first_name="Freeze",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    subscription = Subscription(
        user=client,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=8,
    )
    db_session.add_all([client, subscription])
    await db_session.commit()

    original_end_date = subscription.end_date
    service = SubscriptionService(db_session)

    frozen = await service.freeze(client.id, subscription.id, 10)

    assert frozen.status == SubscriptionStatus.FROZEN
    assert frozen.end_date.replace(tzinfo=UTC) == original_end_date + timedelta(days=10)


@pytest.mark.asyncio
async def test_freeze_rejects_non_active_subscription(db_session):
    client = User(
        email="frozen-client@example.com",
        password_hash="hash",
        first_name="Frozen",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    subscription = Subscription(
        user=client,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.FROZEN,
        total_visits=12,
        remaining_visits=8,
    )
    db_session.add_all([client, subscription])
    await db_session.commit()

    service = SubscriptionService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.freeze(client.id, subscription.id, 7)

    assert error.value.status_code == 400
    assert error.value.detail == "Only active subscriptions can be frozen"
