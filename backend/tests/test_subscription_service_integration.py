from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.membership_plan import MembershipPlan
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.schemas.subscription import SubscriptionManagementIssueRequest, SubscriptionManagementUpdate
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
        "is_public": True,
    }
    payload.update(overrides)
    plan = MembershipPlan(**payload)
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.mark.asyncio
async def test_purchase_uses_real_membership_plan_data(db_session):
    client = User(
        email="plan-client@example.com",
        password_hash="hash",
        first_name="Plan",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add(client)
    await db_session.commit()

    plan = await create_plan(
        db_session,
        title="Річний Flex",
        type=SubscriptionType.YEARLY,
        duration_days=365,
        visits_limit=None,
        price=Decimal("14990.00"),
    )
    service = SubscriptionService(db_session)

    created = await service.purchase(client.id, plan_id=plan.id)

    assert created.plan_id == plan.id
    assert created.type == SubscriptionType.YEARLY
    assert created.total_visits is None
    assert created.remaining_visits is None
    assert created.end_date.replace(tzinfo=UTC).date() == (created.start_date.replace(tzinfo=UTC) + timedelta(days=365)).date()


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


@pytest.mark.asyncio
async def test_management_update_and_delete_store_audit_actor(db_session):
    client = User(
        email="managed-client@example.com",
        password_hash="hash",
        first_name="Managed",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    owner = User(
        email="owner-managed@example.com",
        password_hash="hash",
        first_name="Owner",
        last_name="Manager",
        role=UserRole.OWNER,
        is_verified=True,
    )
    db_session.add_all([client, owner])
    await db_session.commit()

    monthly_plan = await create_plan(db_session)
    yearly_plan = await create_plan(
        db_session,
        title="Річний Flex",
        type=SubscriptionType.YEARLY,
        duration_days=365,
        visits_limit=None,
        price=Decimal("14990.00"),
        sort_order=20,
    )

    service = SubscriptionService(db_session)
    created = await service.purchase(client.id, plan_id=monthly_plan.id)

    updated = await service.update_for_management(
        owner.id,
        created.id,
        payload=SubscriptionManagementUpdate(
            plan_id=yearly_plan.id,
            status=SubscriptionStatus.FROZEN,
            end_date=created.end_date + timedelta(days=5),
        ),
    )

    assert updated.plan_id == yearly_plan.id
    assert updated.status == SubscriptionStatus.FROZEN
    assert updated.last_modified_by_id == owner.id
    assert updated.last_modified_at is not None

    await service.delete_for_management(owner.id, created.id)
    deleted = await service.repository.get_by_id(created.id, include_deleted=True)

    assert deleted is not None
    assert deleted.deleted_by_id == owner.id
    assert deleted.deleted_at is not None
    assert deleted.last_modified_by_id == owner.id


@pytest.mark.asyncio
async def test_management_can_issue_private_plan_and_restore_deleted_subscription(db_session):
    client = User(
        email="private-client@example.com",
        password_hash="hash",
        first_name="Private",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    admin = User(
        email="admin-managed@example.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Manager",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add_all([client, admin])
    await db_session.commit()

    private_plan = await create_plan(
        db_session,
        title="Службовий абонемент",
        is_public=False,
        price=Decimal("1.00"),
    )
    service = SubscriptionService(db_session)

    issued = await service.issue_for_management(
        admin.id,
        SubscriptionManagementIssueRequest(
            user_id=client.id,
            plan_id=private_plan.id,
            status=SubscriptionStatus.ACTIVE,
        ),
    )

    assert issued.plan_id == private_plan.id
    assert issued.last_modified_by_id == admin.id

    await service.delete_for_management(admin.id, issued.id)
    restored = await service.restore_for_management(admin.id, issued.id)

    assert restored.deleted_at is None
    assert restored.deleted_by is None
    assert restored.restored_by_id == admin.id
    assert restored.restored_at is not None
