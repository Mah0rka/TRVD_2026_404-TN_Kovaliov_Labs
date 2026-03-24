from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_create_booking_decrements_remaining_visits(db_session):
    trainer = User(
        email="trainer@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="One",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="One",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    workout_class = WorkoutClass(
        title="Integration Class",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=12,
    )
    db_session.add_all([workout_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    booking = await service.create_booking(client.id, workout_class.id)

    assert booking.user_id == client.id
    assert booking.class_id == workout_class.id
    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 11


@pytest.mark.asyncio
async def test_cancel_booking_returns_visit_for_limited_subscription(db_session):
    trainer = User(
        email="trainer2@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Two",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client2@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Two",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    workout_class = WorkoutClass(
        title="Cancellable Class",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=5,
    )
    db_session.add_all([workout_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    booking = await service.create_booking(client.id, workout_class.id)
    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 4
    await db_session.commit()

    cancelled = await service.cancel_booking(client.id, booking.id)
    assert cancelled.status.value == "CANCELLED"
    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 5


@pytest.mark.asyncio
async def test_create_booking_requires_active_subscription(db_session):
    trainer = User(
        email="trainer3@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Three",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client3@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Three",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    workout_class = WorkoutClass(
        title="Paid Entry Class",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    db_session.add(workout_class)
    await db_session.commit()

    service = BookingService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.create_booking(client.id, workout_class.id)

    assert error.value.status_code == 400
    assert error.value.detail == "An active subscription is required for booking"


@pytest.mark.asyncio
async def test_create_booking_works_when_session_already_has_active_transaction(db_session):
    trainer = User(
        email="trainer4@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Four",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client4@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Four",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    workout_class = WorkoutClass(
        title="Autobegin Safe Class",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=8,
        remaining_visits=8,
    )
    db_session.add_all([workout_class, subscription])
    await db_session.commit()

    # Simulate request flow where the request-scoped session already has an
    # active transaction before the service tries to mutate state.
    await db_session.begin()
    assert db_session.in_transaction()

    service = BookingService(db_session)
    booking = await service.create_booking(client.id, workout_class.id)

    assert booking.user_id == client.id
    assert booking.class_id == workout_class.id
    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 7
