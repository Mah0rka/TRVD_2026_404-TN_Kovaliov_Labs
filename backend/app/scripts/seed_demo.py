import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models.payment import Payment
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType

logger = logging.getLogger(__name__)


async def seed_demo_data() -> None:
    async with async_session_factory() as session:
        users = await _ensure_users(session)
        trainer = users["trainer"]
        client = users["client"]

        await _ensure_schedule(session, trainer)
        await _ensure_subscription(session, client)
        await _ensure_payment(session, client)

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


async def _ensure_subscription(session, client: User) -> None:
    result = await session.execute(select(Subscription).where(Subscription.user_id == client.id))
    if result.scalars().first():
        return

    start_date = datetime.now(UTC)
    session.add(
        Subscription(
            user_id=client.id,
            type=SubscriptionType.MONTHLY,
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
            total_visits=12,
            remaining_visits=12,
            status=SubscriptionStatus.ACTIVE,
        )
    )


async def _ensure_payment(session, client: User) -> None:
    result = await session.execute(select(Payment).where(Payment.user_id == client.id))
    if result.scalars().first():
        return

    session.add(
        Payment(
            user_id=client.id,
            amount=Decimal("990.00"),
            currency="UAH",
            status="SUCCESS",
            method="CARD",
        )
    )


def main() -> None:
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
