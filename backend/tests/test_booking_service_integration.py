# Коротко: тести перевіряють сценарії модуля бронювань.

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.booking import BookingStatus
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
    assert error.value.detail == "Для запису на заняття потрібен активний абонемент"


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


@pytest.mark.asyncio
async def test_free_booking_blocks_second_free_class_on_same_day(db_session):
    trainer = User(
        email="trainer5@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Five",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client5@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Five",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    base_day = (datetime.now(UTC) + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    first_class = WorkoutClass(
        title="Morning Free",
        trainer_id=trainer.id,
        start_time=base_day,
        end_time=base_day + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
    )
    second_class = WorkoutClass(
        title="Evening Free",
        trainer_id=trainer.id,
        start_time=base_day + timedelta(hours=8),
        end_time=base_day + timedelta(hours=9),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
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
    db_session.add_all([first_class, second_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    await service.create_booking(client.id, first_class.id)

    with pytest.raises(HTTPException) as error:
        await service.create_booking(client.id, second_class.id)

    assert error.value.status_code == 400
    assert error.value.detail == "На один день можна записатися лише на одне безкоштовне заняття"


@pytest.mark.asyncio
async def test_paid_booking_is_allowed_as_additional_booking_on_same_day(db_session):
    trainer = User(
        email="trainer6@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Six",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client6@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Six",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = (datetime.now(UTC) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    free_class = WorkoutClass(
        title="Free Group",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
    )
    paid_class = WorkoutClass(
        title="Paid Personal",
        trainer_id=trainer.id,
        start_time=start_time + timedelta(hours=2),
        end_time=start_time + timedelta(hours=3),
        capacity=1,
        type=WorkoutType.PERSONAL,
        is_paid_extra=True,
        extra_price=450,
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
    db_session.add_all([free_class, paid_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    await service.create_booking(client.id, free_class.id)
    pending_payment = await service.create_paid_booking_checkout(client.id, paid_class.id)
    paid_booking = await service.confirm_paid_booking(client.id, pending_payment.id)

    assert paid_booking.class_id == paid_class.id
    assert pending_payment.status == "SUCCESS"
    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 11


@pytest.mark.asyncio
async def test_paid_booking_requires_checkout_confirmation_flow(db_session):
    trainer = User(
        email="trainer8@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Eight",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client8@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Eight",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    paid_class = WorkoutClass(
        title="Paid Personal Flow",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=1,
        type=WorkoutType.PERSONAL,
        is_paid_extra=True,
        extra_price=450,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=6,
    )
    db_session.add_all([paid_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.create_booking(client.id, paid_class.id)

    assert error.value.status_code == 400
    assert error.value.detail == "Для платного заняття спочатку створіть і підтвердьте доплату"

    payment = await service.create_paid_booking_checkout(client.id, paid_class.id)
    assert payment.status == "PENDING"
    assert payment.purpose == "BOOKING_EXTRA"

    booking = await service.confirm_paid_booking(client.id, payment.id)
    assert booking.class_id == paid_class.id

    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 6


@pytest.mark.asyncio
async def test_cancelling_paid_booking_does_not_restore_subscription_visit(db_session):
    trainer = User(
        email="trainer9@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Nine",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client9@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Nine",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1, hours=3)
    paid_class = WorkoutClass(
        title="Paid Cancel",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=1,
        type=WorkoutType.PERSONAL,
        is_paid_extra=True,
        extra_price=350,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=4,
    )
    db_session.add_all([paid_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    payment = await service.create_paid_booking_checkout(client.id, paid_class.id)
    booking = await service.confirm_paid_booking(client.id, payment.id)

    cancelled = await service.cancel_booking(client.id, booking.id)
    assert cancelled.status == BookingStatus.CANCELLED

    await db_session.refresh(subscription)
    assert subscription.remaining_visits == 4


@pytest.mark.asyncio
async def test_free_booking_can_be_cancelled_one_hour_before_start(db_session):
    trainer = User(
        email="trainer7@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Seven",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client7@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Seven",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(minutes=90)
    workout_class = WorkoutClass(
        title="Free Soon",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
    )
    subscription = Subscription(
        user_id=client.id,
        type=SubscriptionType.MONTHLY,
        start_date=datetime.now(UTC),
        end_date=datetime.now(UTC) + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        total_visits=12,
        remaining_visits=3,
    )
    db_session.add_all([workout_class, subscription])
    await db_session.commit()

    service = BookingService(db_session)
    booking = await service.create_booking(client.id, workout_class.id)

    cancelled = await service.cancel_booking(client.id, booking.id)
    assert cancelled.status == BookingStatus.CANCELLED
