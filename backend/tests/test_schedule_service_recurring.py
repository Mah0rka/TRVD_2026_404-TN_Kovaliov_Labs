# Тести перевіряють recurring-сценарії ScheduleService на рівні інтеграції.

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.models.workout_series import RecurrenceFrequency, WorkoutSeries, WorkoutSeriesExclusion
from app.schemas.schedule import (
    RecurrenceScope,
    RecurrenceWeekday,
    ScheduleCompleteRequest,
    ScheduleCreate,
    ScheduleRecurrence,
    ScheduleUpdate,
)
from app.services.schedule_recurrence import serialize_recurrence_rule
from app.services.schedule_service import ScheduleService


KYIV_TZ = ZoneInfo("Europe/Kiev")


def valid_future_slot(days_ahead: int = 2, local_hour: int = 9) -> datetime:
    local_base = datetime.now(KYIV_TZ) + timedelta(days=days_ahead)
    local_start = local_base.replace(hour=local_hour, minute=0, second=0, microsecond=0)
    return local_start.astimezone(UTC)


def weekday_for(start_time: datetime) -> RecurrenceWeekday:
    return list(RecurrenceWeekday)[start_time.astimezone(KYIV_TZ).weekday()]


def make_user(email: str, role: UserRole) -> User:
    return User(
        email=email,
        password_hash="hash",
        first_name=email.split("@", 1)[0],
        last_name="Tester",
        role=role,
        is_verified=True,
    )


async def create_recurring_schedule(
    db_session,
    trainer: User,
    *,
    title: str = "Recurring Class",
    count: int = 4,
    local_hour: int = 9,
    days_ahead: int = 2,
    is_paid_extra: bool = False,
    extra_price=None,
):
    service = ScheduleService(db_session)
    start_time = valid_future_slot(days_ahead=days_ahead, local_hour=local_hour)
    created = await service.create_schedule(
        ScheduleCreate(
            title=title,
            type=WorkoutType.GROUP,
            startTime=start_time,
            endTime=start_time + timedelta(hours=1),
            capacity=12,
            trainerId=trainer.id,
            isPaidExtra=is_paid_extra,
            extraPrice=extra_price,
            recurrence=ScheduleRecurrence(
                frequency=RecurrenceFrequency.WEEKLY,
                interval=1,
                byWeekday=[weekday_for(start_time)],
                count=count,
            ),
        ),
        trainer,
    )
    occurrences = await service.list_schedules(start_time - timedelta(days=1), start_time + timedelta(days=90))
    recurring = sorted(
        [item for item in occurrences if item.series_id == created.series_id],
        key=lambda item: item.start_time,
    )
    return service, created, recurring


# Перевіряє, що list schedules і list my classes поважають фільтри.
@pytest.mark.asyncio
async def test_schedule_service_lists_filtered_classes_and_my_classes(db_session):
    trainer = make_user("filter-trainer@example.com", UserRole.TRAINER)
    other_trainer = make_user("other-filter-trainer@example.com", UserRole.TRAINER)
    first_start = valid_future_slot(days_ahead=2, local_hour=9)
    second_start = valid_future_slot(days_ahead=5, local_hour=10)
    db_session.add_all(
        [
            trainer,
            other_trainer,
            WorkoutClass(
                title="Target Class",
                trainer=trainer,
                start_time=first_start,
                end_time=first_start + timedelta(hours=1),
                capacity=10,
                type=WorkoutType.GROUP,
            ),
            WorkoutClass(
                title="Other Class",
                trainer=other_trainer,
                start_time=second_start,
                end_time=second_start + timedelta(hours=1),
                capacity=10,
                type=WorkoutType.GROUP,
            ),
        ]
    )
    await db_session.commit()

    service = ScheduleService(db_session)
    filtered = await service.list_schedules(first_start - timedelta(minutes=5), first_start + timedelta(minutes=5))
    my_classes = await service.list_my_classes(
        trainer.id,
        first_start - timedelta(days=1),
        first_start + timedelta(days=1),
    )

    assert [item.title for item in filtered] == ["Target Class"]
    assert [item.title for item in my_classes] == ["Target Class"]


# Перевіряє, що paid extra schedule вимагає додаткову вартість.
@pytest.mark.asyncio
async def test_create_schedule_rejects_paid_extra_without_price(db_session):
    admin = make_user("pricing-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = valid_future_slot()

    with pytest.raises(HTTPException) as error:
        await service.create_schedule(
            ScheduleCreate(
                title="Paid Class",
                type=WorkoutType.PERSONAL,
                startTime=start_time,
                endTime=start_time + timedelta(hours=1),
                capacity=1,
                trainerId=admin.id,
                isPaidExtra=True,
            ),
            admin,
        )

    assert error.value.detail == "Для платного заняття потрібно вказати додаткову вартість"


# Перевіряє, що create schedule реагує на порожню materialization recurring-серії.
@pytest.mark.asyncio
async def test_create_schedule_recurring_raises_when_materialization_returns_empty(db_session):
    admin = make_user("empty-series-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service = ScheduleService(db_session)
    service._materialize_series_occurrences = AsyncMock(return_value=[])
    start_time = valid_future_slot()

    with pytest.raises(HTTPException) as error:
        await service.create_schedule(
            ScheduleCreate(
                title="Empty Series",
                type=WorkoutType.GROUP,
                startTime=start_time,
                endTime=start_time + timedelta(hours=1),
                capacity=8,
                trainerId=admin.id,
                recurrence=ScheduleRecurrence(
                    frequency=RecurrenceFrequency.WEEKLY,
                    interval=1,
                    byWeekday=[weekday_for(start_time)],
                    count=3,
                ),
            ),
            admin,
        )

    assert error.value.detail == "Не вдалося згенерувати occurrences для recurring-серії"


# Перевіряє, що update schedule блокує missing-class і recurrence для одиночного заняття.
@pytest.mark.asyncio
async def test_update_schedule_rejects_missing_class_and_non_series_recurrence(db_session):
    admin = make_user("update-admin@example.com", UserRole.ADMIN)
    standalone_start = valid_future_slot()
    standalone_class = WorkoutClass(
        title="Standalone",
        trainer=admin,
        start_time=standalone_start,
        end_time=standalone_start + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([admin, standalone_class])
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as missing_error:
        await service.update_schedule("missing-class", ScheduleUpdate(title="Missing"), admin)
    assert missing_error.value.detail == "Class not found"

    with pytest.raises(HTTPException) as recurrence_error:
        await service.update_schedule(
            standalone_class.id,
            ScheduleUpdate(
                recurrence=ScheduleRecurrence(
                    frequency=RecurrenceFrequency.WEEKLY,
                    byWeekday=[weekday_for(standalone_start)],
                    count=2,
                )
            ),
            admin,
        )
    assert recurrence_error.value.detail == "Recurring можна додати лише під час створення нової серії"


# Перевіряє, що missing-class гілки працюють для completion і attendees.
@pytest.mark.asyncio
async def test_completion_and_attendees_raise_for_missing_class(db_session):
    trainer = make_user("missing-class-trainer@example.com", UserRole.TRAINER)
    db_session.add(trainer)
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as completion_error:
        await service.confirm_completion(
            "missing-class",
            ScheduleCompleteRequest(comment="done"),
            trainer,
        )
    assert completion_error.value.detail == "Class not found"

    with pytest.raises(HTTPException) as attendees_error:
        await service.list_attendees("missing-class", trainer)
    assert attendees_error.value.detail == "Class not found"


# Перевіряє, що завершення заняття не може підтвердити сторонній тренер.
@pytest.mark.asyncio
async def test_confirm_completion_rejects_foreign_trainer(db_session):
    owner_trainer = make_user("owner-completion@example.com", UserRole.TRAINER)
    other_trainer = make_user("other-completion@example.com", UserRole.TRAINER)
    class_start = datetime.now(UTC) - timedelta(hours=3)
    workout_class = WorkoutClass(
        title="Protected Completion",
        trainer=owner_trainer,
        start_time=class_start,
        end_time=class_start + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([owner_trainer, other_trainer, workout_class])
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.confirm_completion(
            workout_class.id,
            ScheduleCompleteRequest(comment="forbidden"),
            other_trainer,
        )

    assert error.value.detail == "Недостатньо прав доступу"


# Перевіряє, що update occurrence позначає exception і чистить extra price.
@pytest.mark.asyncio
async def test_update_occurrence_marks_series_exception_and_clears_extra_price(db_session):
    admin = make_user("occurrence-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, _ = await create_recurring_schedule(
        db_session,
        admin,
        title="Paid Series",
        count=2,
        is_paid_extra=True,
        extra_price=25,
    )

    updated = await service.update_schedule(
        created.id,
        ScheduleUpdate(isPaidExtra=False, scope=RecurrenceScope.OCCURRENCE),
        admin,
    )

    assert updated.is_series_exception is True
    assert updated.extra_price is None
    assert updated.series_id == created.series_id


# Перевіряє, що occurrence update не приймає нове recurrence-правило.
@pytest.mark.asyncio
async def test_update_occurrence_rejects_inline_recurrence_rule(db_session):
    admin = make_user("inline-recurrence-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, _ = await create_recurring_schedule(db_session, admin, count=2)

    with pytest.raises(HTTPException) as error:
        await service.update_schedule(
            created.id,
            ScheduleUpdate(
                scope=RecurrenceScope.OCCURRENCE,
                recurrence=ScheduleRecurrence(
                    frequency=RecurrenceFrequency.WEEKLY,
                    byWeekday=[weekday_for(created.start_time)],
                    count=2,
                ),
            ),
            admin,
        )

    assert error.value.detail == "Recurring-правило можна змінювати лише для scope following або series"


# Перевіряє, що update following split-ить серію на стару і нову частину.
@pytest.mark.asyncio
async def test_update_following_splits_series(db_session):
    admin = make_user("following-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, recurring = await create_recurring_schedule(db_session, admin, count=4)
    second_occurrence = recurring[1]

    updated = await service.update_schedule(
        second_occurrence.id,
        ScheduleUpdate(
            title="Split Series",
            startTime=second_occurrence.start_time + timedelta(hours=1),
            endTime=second_occurrence.end_time + timedelta(hours=1),
            scope=RecurrenceScope.FOLLOWING,
            recurrence=ScheduleRecurrence(
                frequency=RecurrenceFrequency.WEEKLY,
                interval=1,
                byWeekday=[weekday_for(second_occurrence.start_time)],
                count=3,
            ),
        ),
        admin,
    )
    all_occurrences = await service.list_schedules(created.start_time - timedelta(days=1), created.start_time + timedelta(days=90))
    related = sorted(
        [
            item
            for item in all_occurrences
            if item.title in {"Recurring Class", "Split Series"}
            and item.trainer_id == admin.id
        ],
        key=lambda item: item.start_time,
    )

    assert updated.series_id is not None
    assert updated.series_id != created.series_id
    assert related[0].title == "Recurring Class"
    assert [item.title for item in related[1:]] == ["Split Series", "Split Series", "Split Series"]


# Перевіряє, що update series переписує всі майбутні occurrences однієї серії.
@pytest.mark.asyncio
async def test_update_series_rewrites_future_occurrences(db_session):
    admin = make_user("series-rewrite-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, _ = await create_recurring_schedule(db_session, admin, count=3)

    updated = await service.update_schedule(
        created.id,
        ScheduleUpdate(
            title="Whole Series Updated",
            capacity=20,
            isPaidExtra=False,
            scope=RecurrenceScope.SERIES,
            recurrence=ScheduleRecurrence(
                frequency=RecurrenceFrequency.WEEKLY,
                interval=1,
                byWeekday=[weekday_for(created.start_time)],
                count=3,
            ),
        ),
        admin,
    )
    occurrences = await service.list_schedules(created.start_time - timedelta(days=1), created.start_time + timedelta(days=90))
    recurring = [item for item in occurrences if item.series_id == created.series_id]

    assert updated.title == "Whole Series Updated"
    assert len(recurring) == 3
    assert all(item.title == "Whole Series Updated" for item in recurring)
    assert all(item.capacity == 20 for item in recurring)


# Перевіряє, що delete occurrence для серії створює exclusion і видаляє лише одну дату.
@pytest.mark.asyncio
async def test_delete_occurrence_for_series_creates_exclusion(db_session):
    admin = make_user("delete-occurrence-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, recurring = await create_recurring_schedule(db_session, admin, count=3)
    await service.delete_schedule(recurring[1].id, admin, RecurrenceScope.OCCURRENCE)

    exclusions = await db_session.execute(
        select(WorkoutSeriesExclusion).where(WorkoutSeriesExclusion.series_id == created.series_id)
    )
    remaining = await service.list_schedules(created.start_time - timedelta(days=1), created.start_time + timedelta(days=90))
    recurring_remaining = [item for item in remaining if item.series_id == created.series_id]

    assert len(recurring_remaining) == 2
    assert exclusions.scalar_one_or_none() is not None


# Перевіряє, що delete occurrence блокується при confirmed booking.
@pytest.mark.asyncio
async def test_delete_occurrence_rejects_confirmed_booking(db_session):
    admin = make_user("delete-block-admin@example.com", UserRole.ADMIN)
    client = make_user("delete-block-client@example.com", UserRole.CLIENT)
    class_start = valid_future_slot()
    workout_class = WorkoutClass(
        title="Booked Class",
        trainer=admin,
        start_time=class_start,
        end_time=class_start + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([admin, client, workout_class])
    await db_session.flush()
    db_session.add(Booking(user_id=client.id, class_id=workout_class.id, status=BookingStatus.CONFIRMED))
    await db_session.commit()

    service = ScheduleService(db_session)

    with pytest.raises(HTTPException) as error:
        await service.delete_schedule(workout_class.id, admin, RecurrenceScope.OCCURRENCE)

    assert error.value.detail == "Не можна видалити заняття, поки в ньому є підтверджені записи"


# Перевіряє, що delete schedule реагує на missing-class і forbidden actor.
@pytest.mark.asyncio
async def test_delete_schedule_rejects_missing_class_and_forbidden_user(db_session):
    admin = make_user("delete-missing-admin@example.com", UserRole.ADMIN)
    trainer = make_user("delete-forbidden-trainer@example.com", UserRole.TRAINER)
    db_session.add_all([admin, trainer])
    await db_session.commit()
    service, created, _ = await create_recurring_schedule(db_session, admin, count=2)

    with pytest.raises(HTTPException) as missing_error:
        await service.delete_schedule("missing-class", admin, RecurrenceScope.OCCURRENCE)
    assert missing_error.value.detail == "Class not found"

    with pytest.raises(HTTPException) as forbidden_error:
        await service.delete_schedule(created.id, trainer, RecurrenceScope.OCCURRENCE)
    assert forbidden_error.value.detail == "Недостатньо прав доступу"


# Перевіряє, що delete following лишає попередні occurrences і видаляє всі наступні.
@pytest.mark.asyncio
async def test_delete_following_keeps_previous_occurrences(db_session):
    admin = make_user("delete-following-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, recurring = await create_recurring_schedule(db_session, admin, count=4)
    await service.delete_schedule(recurring[1].id, admin, RecurrenceScope.FOLLOWING)

    remaining = await service.list_schedules(created.start_time - timedelta(days=1), created.start_time + timedelta(days=90))
    recurring_remaining = [item for item in remaining if item.series_id == created.series_id]

    assert len(recurring_remaining) == 1
    assert recurring_remaining[0].id == recurring[0].id


# Перевіряє, що delete series до старту прибирає series-запис і всі її occurrences.
@pytest.mark.asyncio
async def test_delete_series_before_start_removes_occurrences_and_series(db_session):
    admin = make_user("delete-series-admin@example.com", UserRole.ADMIN)
    db_session.add(admin)
    await db_session.commit()

    service, created, recurring = await create_recurring_schedule(db_session, admin, count=3, days_ahead=5)
    await service.delete_schedule(recurring[0].id, admin, RecurrenceScope.SERIES)

    series_result = await db_session.execute(select(WorkoutSeries).where(WorkoutSeries.id == created.series_id))
    remaining = await service.list_schedules(created.start_time - timedelta(days=1), created.start_time + timedelta(days=90))
    recurring_remaining = [item for item in remaining if item.series_id == created.series_id]

    assert series_result.scalar_one_or_none() is None
    assert recurring_remaining == []


# Перевіряє, що materialization створює лише відсутні occurrences і пропускає exclusions.
@pytest.mark.asyncio
async def test_materialize_future_occurrences_adds_only_missing_occurrences(db_session):
    trainer = make_user("materialize-admin@example.com", UserRole.ADMIN)
    db_session.add(trainer)
    await db_session.commit()

    service = ScheduleService(db_session)
    start_time = valid_future_slot(days_ahead=1)
    recurrence = ScheduleRecurrence(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        byWeekday=[weekday_for(start_time)],
        count=3,
    )
    third_occurrence_start = start_time + timedelta(days=14)

    series = WorkoutSeries(
        title="Materialized Series",
        description=None,
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday=weekday_for(start_time).value,
        count=3,
        until=None,
        rule_text=serialize_recurrence_rule(start_time, recurrence),
    )
    db_session.add(series)
    await db_session.flush()
    db_session.add(
        WorkoutClass(
            title=series.title,
            trainer_id=trainer.id,
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            capacity=10,
            type=WorkoutType.GROUP,
            series_id=series.id,
            source_occurrence_start=start_time,
        )
    )
    db_session.add(
        WorkoutSeriesExclusion(
            series_id=series.id,
            occurrence_start=start_time + timedelta(days=7),
        )
    )
    await db_session.commit()

    created_count = await service.materialize_future_occurrences()

    occurrences = await service.list_schedules(start_time - timedelta(days=1), third_occurrence_start + timedelta(days=1))
    recurring = sorted([item for item in occurrences if item.series_id == series.id], key=lambda item: item.start_time)

    assert created_count == 1
    assert [
        (item.source_occurrence_start.replace(tzinfo=UTC) if item.source_occurrence_start.tzinfo is None else item.source_occurrence_start)
        for item in recurring
    ] == [
        start_time,
        third_occurrence_start,
    ]
