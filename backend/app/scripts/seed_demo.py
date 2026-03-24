import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models.booking import Booking
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType

logger = logging.getLogger(__name__)


async def seed_demo_data() -> None:
    async with async_session_factory() as session:
        users = await _ensure_users(session)
        plans = await _ensure_membership_plans(session)
        await _reconcile_legacy_demo_users(session, users)
        await _attach_plans_to_existing_subscriptions(session, plans)
        trainer = users["trainer"]
        client = users["client"]

        await _ensure_schedule(session, trainer)
        await _ensure_subscription(session, client, plans["monthly"])
        await _ensure_payment(session, client, plans["monthly"])

        await session.commit()
        logger.info("Demo seed completed successfully")


async def _ensure_users(session) -> dict[str, User]:
    definitions = {
        "owner": ("owner@example.com", "Owner", "Account", UserRole.OWNER),
        "admin": ("admin@example.com", "Admin", "Account", UserRole.ADMIN),
        "trainer": ("trainer@example.com", "Trainer", "Account", UserRole.TRAINER),
        "client": ("client@example.com", "Client", "Account", UserRole.CLIENT),
    }

    created: dict[str, User] = {}
    for key, (email, first_name, last_name, role) in definitions.items():
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                password_hash=hash_password("Password123!"),
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_verified=True,
            )
            session.add(user)
            await session.flush()
        created[key] = user

    return created


async def _ensure_membership_plans(session) -> dict[str, MembershipPlan]:
    definitions = {
        "monthly": {
            "title": "Місячний абонемент",
            "description": "12 занять у клубі протягом 30 днів.",
            "type": SubscriptionType.MONTHLY,
            "duration_days": 30,
            "visits_limit": 12,
            "price": Decimal("990.00"),
            "currency": "UAH",
            "sort_order": 10,
            "is_active": True,
            "is_public": True,
        },
        "yearly": {
            "title": "Річний абонемент",
            "description": "Річний доступ до клубу без ліміту занять.",
            "type": SubscriptionType.YEARLY,
            "duration_days": 365,
            "visits_limit": None,
            "price": Decimal("1490.00"),
            "currency": "UAH",
            "sort_order": 20,
            "is_active": True,
            "is_public": True,
        },
        "dropin": {
            "title": "Разове відвідування",
            "description": "Один візит у клуб протягом 30 днів.",
            "type": SubscriptionType.PAY_AS_YOU_GO,
            "duration_days": 30,
            "visits_limit": 1,
            "price": Decimal("190.00"),
            "currency": "UAH",
            "sort_order": 30,
            "is_active": True,
            "is_public": True,
        },
        "private_comp": {
            "title": "Службовий абонемент",
            "description": "Непублічний план для ручної видачі клієнтам.",
            "type": SubscriptionType.MONTHLY,
            "duration_days": 30,
            "visits_limit": 12,
            "price": Decimal("1.00"),
            "currency": "UAH",
            "sort_order": 40,
            "is_active": True,
            "is_public": False,
        },
    }

    created: dict[str, MembershipPlan] = {}
    for key, payload in definitions.items():
        result = await session.execute(select(MembershipPlan).where(MembershipPlan.title == payload["title"]))
        plan = result.scalar_one_or_none()
        if not plan:
            plan = MembershipPlan(**payload)
            session.add(plan)
            await session.flush()
        else:
            for field, value in payload.items():
                setattr(plan, field, value)
        created[key] = plan

    return created


async def _reconcile_legacy_demo_users(session, canonical_users: dict[str, User]) -> None:
    legacy_emails = {
        "owner@fcms.local": "owner",
        "admin@fcms.local": "admin",
        "trainer@fcms.local": "trainer",
        "client@fcms.local": "client",
    }

    for legacy_email, canonical_key in legacy_emails.items():
        result = await session.execute(select(User).where(User.email == legacy_email))
        legacy_user = result.scalar_one_or_none()
        if not legacy_user:
            continue

        canonical_user = canonical_users[canonical_key]
        await _migrate_user_relations(session, legacy_user, canonical_user)
        await session.delete(legacy_user)
        await session.flush()


async def _migrate_user_relations(session, source_user: User, target_user: User) -> None:
    if source_user.id == target_user.id:
        return

    subscription_result = await session.execute(
        select(Subscription).where(Subscription.user_id == source_user.id)
    )
    for subscription in subscription_result.scalars().all():
        subscription.user_id = target_user.id

    payment_result = await session.execute(select(Payment).where(Payment.user_id == source_user.id))
    for payment in payment_result.scalars().all():
        payment.user_id = target_user.id

    booking_result = await session.execute(select(Booking).where(Booking.user_id == source_user.id))
    for booking in booking_result.scalars().all():
        booking.user_id = target_user.id

    class_result = await session.execute(
        select(WorkoutClass).where(WorkoutClass.trainer_id == source_user.id)
    )
    for workout_class in class_result.scalars().all():
        workout_class.trainer_id = target_user.id


async def _ensure_schedule(session, trainer: User) -> None:
    result = await session.execute(select(WorkoutClass).limit(1))
    if result.scalar_one_or_none():
        return

    first_start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=1, hours=8)
    second_start = first_start + timedelta(days=1)
    session.add_all(
        [
            WorkoutClass(
                title="Morning Mobility",
                trainer_id=trainer.id,
                start_time=first_start,
                end_time=first_start + timedelta(hours=1),
                capacity=12,
                type=WorkoutType.GROUP,
            ),
            WorkoutClass(
                title="Personal Strength Session",
                trainer_id=trainer.id,
                start_time=second_start,
                end_time=second_start + timedelta(hours=1),
                capacity=1,
                type=WorkoutType.PERSONAL,
            ),
        ]
    )


async def _ensure_subscription(session, client: User, plan: MembershipPlan) -> None:
    result = await session.execute(select(Subscription).where(Subscription.user_id == client.id))
    if result.scalars().first():
        return

    start_date = datetime.now(UTC)
    session.add(
        Subscription(
            user_id=client.id,
            plan_id=plan.id,
            type=plan.type,
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
            total_visits=plan.visits_limit,
            remaining_visits=plan.visits_limit,
            status=SubscriptionStatus.ACTIVE,
        )
    )


async def _ensure_payment(session, client: User, plan: MembershipPlan) -> None:
    result = await session.execute(select(Payment).where(Payment.user_id == client.id))
    if result.scalars().first():
        return

    session.add(
        Payment(
            user_id=client.id,
            amount=plan.price,
            currency=plan.currency,
            status="SUCCESS",
            method="CARD",
        )
    )


async def _attach_plans_to_existing_subscriptions(session, plans: dict[str, MembershipPlan]) -> None:
    result = await session.execute(select(Subscription))
    subscriptions = result.scalars().all()
    for subscription in subscriptions:
        if subscription.plan_id:
            continue
        if subscription.type == SubscriptionType.MONTHLY:
            subscription.plan_id = plans["monthly"].id
        elif subscription.type == SubscriptionType.YEARLY:
            subscription.plan_id = plans["yearly"].id
        elif subscription.type == SubscriptionType.PAY_AS_YOU_GO:
            subscription.plan_id = plans["dropin"].id


def main() -> None:
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
