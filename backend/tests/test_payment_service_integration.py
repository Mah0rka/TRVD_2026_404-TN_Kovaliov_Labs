from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment
from app.models.subscription import SubscriptionType
from app.models.user import User, UserRole
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService


async def create_plan(db_session, **overrides) -> MembershipPlan:
    payload = {
        "title": "Місячний",
        "description": "12 занять",
        "type": SubscriptionType.MONTHLY,
        "duration_days": 30,
        "visits_limit": 12,
        "price": Decimal("990.00"),
        "currency": "UAH",
        "sort_order": 10,
        "is_active": True,
    }
    payload.update(overrides)
    plan = MembershipPlan(**payload)
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.mark.asyncio
async def test_subscription_purchase_creates_fixed_price_payment(db_session):
    client = User(
        email="billing-client@example.com",
        password_hash="hash",
        first_name="Billing",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add(client)
    await db_session.commit()

    plan = await create_plan(db_session)
    subscription_service = SubscriptionService(db_session)
    payment_service = PaymentService(db_session)

    subscription = await subscription_service.purchase(client.id, plan_id=plan.id)
    payments = await payment_service.list_for_user(client.id)

    assert subscription.type == SubscriptionType.MONTHLY
    assert len(payments) == 1
    assert str(payments[0].amount) == "990.00"
    assert payments[0].method == "CARD"
    assert payments[0].status == "SUCCESS"


@pytest.mark.asyncio
async def test_payment_service_rejects_direct_top_up(db_session):
    service = PaymentService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.checkout("user-1", Decimal("100.00"), "card")

    assert error.value.status_code == 410


@pytest.mark.asyncio
async def test_payment_history_shows_subscription_purchases_only(db_session):
    client = User(
        email="history-client@example.com",
        password_hash="hash",
        first_name="History",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add(client)
    await db_session.commit()

    plan = await create_plan(db_session)
    subscription_service = SubscriptionService(db_session)
    payment_service = PaymentService(db_session)

    await subscription_service.purchase(client.id, plan_id=plan.id)
    db_session.add(
        Payment(
            user_id=client.id,
            amount=Decimal("197.00"),
            currency="UAH",
            status="SUCCESS",
            method="CARD",
        )
    )
    await db_session.commit()

    payments = await payment_service.list_for_user(client.id)
    stored = await db_session.execute(select(Payment).where(Payment.user_id == client.id))

    assert len(stored.scalars().all()) == 2
    assert len(payments) == 1
    assert str(payments[0].amount) == "990.00"


@pytest.mark.asyncio
async def test_subscription_purchase_rejects_second_active_membership(db_session):
    client = User(
        email="duplicate-membership@example.com",
        password_hash="hash",
        first_name="Duplicate",
        last_name="Membership",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add(client)
    await db_session.commit()

    subscription_service = SubscriptionService(db_session)
    first_plan = await create_plan(db_session)
    second_plan = await create_plan(
        db_session,
        title="Річний",
        type=SubscriptionType.YEARLY,
        duration_days=365,
        visits_limit=None,
        price=Decimal("14990.00"),
        sort_order=20,
    )
    await subscription_service.purchase(client.id, plan_id=first_plan.id)

    with pytest.raises(HTTPException) as error:
        await subscription_service.purchase(client.id, plan_id=second_plan.id)

    assert error.value.status_code == 409
    assert error.value.detail == "Finish or pause your current membership before purchasing a new one"
