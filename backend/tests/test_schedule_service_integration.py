# Тести перевіряють ключові сценарії цього модуля.

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.models.workout_series import RecurrenceFrequency
from app.schemas.schedule import (
    RecurrenceScope,
    RecurrenceWeekday,
    ScheduleCompleteRequest,
    ScheduleCreate,
    ScheduleRecurrence,
    ScheduleUpdate,
)
from app.services.schedule_service import ScheduleService


KYIV_TZ = ZoneInfo("Europe/Kiev")


def valid_future_slot(days_ahead: int = 2, local_hour: int = 9) -> datetime:
    local_base = datetime.now(KYIV_TZ) + timedelta(days=days_ahead)
    local_start = local_base.replace(
        hour=local_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    return local_start.astimezone(UTC)


# Перевіряє, що create schedule uses current trainer when trainer id missing працює коректно.
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
    start_time = valid_future_slot()
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


# Перевіряє, що create schedule rejects classes outside club working hours.
@pytest.mark.asyncio
async def test_create_schedule_rejects_outside_club_hours(db_session):
    admin = User(
        email="late-admin@example.com",
        password_hash="hash",
        first_name="Late",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = datetime(2026, 3, 29, 18, 0, tzinfo=UTC)
    end_time = datetime(2026, 3, 29, 20, 0, tzinfo=UTC)

    with pytest.raises(HTTPException) as error:
        await service.create_schedule(
            ScheduleCreate(
                title="Too Late",
                type=WorkoutType.GROUP,
                startTime=start_time,
                endTime=end_time,
                capacity=10,
                trainerId=admin.id,
            ),
            admin,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Заняття можна планувати лише в межах роботи клубу: 06:00-22:00"


# Перевіряє, що update schedule rejects invalid time range працює коректно.
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
    class_start = valid_future_slot(days_ahead=1)
    workout_class = WorkoutClass(
        title="Evening Class",
        trainer=trainer,
        start_time=class_start,
        end_time=class_start + timedelta(hours=1),
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
            trainer,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Час завершення має бути пізніше за час початку"


# Перевіряє, що list attendees allows trainer and blocks other roles працює коректно.
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
    class_start = valid_future_slot(days_ahead=1)
    workout_class = WorkoutClass(
        title="Access Controlled Class",
        trainer=trainer,
        start_time=class_start,
        end_time=class_start + timedelta(hours=1),
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


# Перевіряє, що завершене заняття може підтвердити тренер з коментарем.
@pytest.mark.asyncio
async def test_confirm_completion_sets_comment_and_actor(db_session):
    trainer = User(
        email="completion-trainer@example.com",
        password_hash="hash",
        first_name="Trainer",
        last_name="Done",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    workout_class = WorkoutClass(
        title="Completed Class",
        trainer=trainer,
        start_time=datetime.now(UTC) - timedelta(hours=2),
        end_time=datetime.now(UTC) - timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([trainer, workout_class])
    await db_session.commit()

    service = ScheduleService(db_session)
    completed = await service.confirm_completion(
        workout_class.id,
        ScheduleCompleteRequest(comment="Група відпрацювала весь план."),
        trainer,
    )

    assert completed.completed_at is not None
    assert completed.completed_by is not None
    assert completed.completed_by.id == trainer.id
    assert completed.completion_comment == "Група відпрацювала весь план."


# Перевіряє, що завершення не можна підтвердити до фактичного кінця заняття.
@pytest.mark.asyncio
async def test_confirm_completion_rejects_active_class(db_session):
    trainer = User(
        email="completion-early@example.com",
        password_hash="hash",
        first_name="Trainer",
        last_name="Early",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    workout_class = WorkoutClass(
        title="Still Running",
        trainer=trainer,
        start_time=datetime.now(UTC) - timedelta(minutes=15),
        end_time=datetime.now(UTC) + timedelta(minutes=45),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([trainer, workout_class])
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.confirm_completion(
            workout_class.id,
            ScheduleCompleteRequest(comment="Too early"),
            trainer,
        )

    assert error.value.status_code == 400
    assert error.value.detail == "Заняття можна підтвердити лише після завершення"


# Перевіряє, що створення recurring-серії materializes очікувані occurrences.
@pytest.mark.asyncio
async def test_create_schedule_with_recurrence_materializes_occurrences(db_session):
    trainer = User(
        email="series-trainer@example.com",
        password_hash="hash",
        first_name="Series",
        last_name="Trainer",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(trainer)
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = valid_future_slot()
    created = await service.create_schedule(
        ScheduleCreate(
            title="Recurring Flow",
            type=WorkoutType.GROUP,
            startTime=start_time,
            endTime=start_time + timedelta(hours=1),
            capacity=10,
            trainerId=trainer.id,
            recurrence=ScheduleRecurrence(
                frequency=RecurrenceFrequency.WEEKLY,
                interval=1,
                byWeekday=[RecurrenceWeekday.MO, RecurrenceWeekday.WE],
                count=4,
            ),
        ),
        trainer,
    )

    schedules = await service.list_schedules(start_time, start_time + timedelta(days=30))
    recurring = [item for item in schedules if item.series_id == created.series_id]
    assert created.series_id is not None
    assert len(recurring) == 4
    assert all(item.recurrence is not None for item in recurring)


# Перевіряє, що тренер може редагувати лише власне заняття.
@pytest.mark.asyncio
async def test_update_schedule_allows_trainer_only_for_owned_class(db_session):
    owner_trainer = User(
        email="owned-trainer@example.com",
        password_hash="hash",
        first_name="Owned",
        last_name="Trainer",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    other_trainer = User(
        email="other-trainer@example.com",
        password_hash="hash",
        first_name="Other",
        last_name="Trainer",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    class_start = valid_future_slot()
    workout_class = WorkoutClass(
        title="Owned Class",
        trainer=owner_trainer,
        start_time=class_start,
        end_time=class_start + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([owner_trainer, other_trainer, workout_class])
    await db_session.commit()

    service = ScheduleService(db_session)
    updated = await service.update_schedule(
        workout_class.id,
        ScheduleUpdate(title="Updated By Owner"),
        owner_trainer,
    )
    assert updated.title == "Updated By Owner"

    with pytest.raises(HTTPException) as error:
        await service.update_schedule(
            workout_class.id,
            ScheduleUpdate(title="Forbidden"),
            other_trainer,
        )

    assert error.value.status_code == 403


# Перевіряє, що recurring delete блокується, якщо є confirmed bookings.
@pytest.mark.asyncio
async def test_delete_schedule_blocks_series_scope_with_confirmed_bookings(db_session):
    admin = User(
        email="series-admin@example.com",
        password_hash="hash",
        first_name="Series",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    client = User(
        email="series-client@example.com",
        password_hash="hash",
        first_name="Series",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([admin, client])
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = valid_future_slot(days_ahead=3)
    created = await service.create_schedule(
        ScheduleCreate(
            title="Protected Series",
            type=WorkoutType.GROUP,
            startTime=start_time,
            endTime=start_time + timedelta(hours=1),
            capacity=12,
            trainerId=admin.id,
            recurrence=ScheduleRecurrence(
                frequency=RecurrenceFrequency.WEEKLY,
                interval=1,
                byWeekday=[RecurrenceWeekday(start_time.strftime("%a")[:2].upper())],
                count=3,
            ),
        ),
        admin,
    )

    booking = Booking(user_id=client.id, class_id=created.id, status=BookingStatus.CONFIRMED)
    db_session.add(booking)
    await db_session.commit()

    with pytest.raises(HTTPException) as error:
        await service.delete_schedule(created.id, admin, RecurrenceScope.SERIES)

    assert error.value.status_code == 400
    assert "підтверджені записи" in error.value.detail
