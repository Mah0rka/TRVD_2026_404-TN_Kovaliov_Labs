from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.schedule_service import ScheduleService


@pytest.mark.asyncio
async def test_create_schedule_uses_current_trainer_when_trainer_id_missing(db_session):
    trainer = User(
        email="schedule-trainer@example.com",
        password_hash="hash",
        first_name="Schedule",
        last_name="Trainer",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    db_session.add(trainer)
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = datetime.now(UTC) + timedelta(days=2)
    created = await service.create_schedule(
        ScheduleCreate(
            title=" Morning Burn ",
            type=WorkoutType.GROUP,
            startTime=start_time,
            endTime=start_time + timedelta(hours=1),
            capacity=14,
        ),
        trainer,
    )

    assert created.title == "Morning Burn"
    assert created.trainer_id == trainer.id
    assert created.capacity == 14
    assert created.is_paid_extra is False
    assert created.extra_price is None


@pytest.mark.asyncio
async def test_update_schedule_rejects_invalid_time_range(db_session):
    trainer = User(
        email="update-trainer@example.com",
        password_hash="hash",
        first_name="Update",
        last_name="Trainer",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    workout_class = WorkoutClass(
        title="Evening Class",
        trainer=trainer,
        start_time=datetime.now(UTC) + timedelta(days=1),
        end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([trainer, workout_class])
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.update_schedule(
            workout_class.id,
            ScheduleUpdate(
                startTime=workout_class.start_time + timedelta(hours=3),
                endTime=workout_class.start_time + timedelta(hours=2),
            ),
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Час завершення має бути пізніше за час початку"


@pytest.mark.asyncio
async def test_list_attendees_allows_trainer_and_blocks_other_roles(db_session):
    trainer = User(
        email="attendees-trainer@example.com",
        password_hash="hash",
        first_name="Trainer",
        last_name="Owner",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    stranger = User(
        email="stranger-client@example.com",
        password_hash="hash",
        first_name="Other",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    attendee = User(
        email="attendee@example.com",
        password_hash="hash",
        first_name="Attendee",
        last_name="One",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    workout_class = WorkoutClass(
        title="Access Controlled Class",
        trainer=trainer,
        start_time=datetime.now(UTC) + timedelta(days=1),
        end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([trainer, stranger, attendee, workout_class])
    await db_session.flush()
    db_session.add(
        Booking(
            user_id=attendee.id,
            class_id=workout_class.id,
            status=BookingStatus.CONFIRMED,
        )
    )
    await db_session.commit()

    service = ScheduleService(db_session)

    attendees = await service.list_attendees(workout_class.id, trainer)
    assert len(attendees) == 1
    assert attendees[0].user.email == attendee.email

    with pytest.raises(HTTPException) as error:
        await service.list_attendees(workout_class.id, stranger)

    assert error.value.status_code == 403
    assert error.value.detail == "Недостатньо прав доступу"
