# Тести перевіряють приватні helper-методи ScheduleService.

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.booking import BookingStatus
from app.models.user import UserRole
from app.models.workout_class import WorkoutType
from app.models.workout_series import RecurrenceFrequency
from app.schemas.schedule import RecurrenceScope, RecurrenceWeekday, ScheduleRecurrence, ScheduleUpdate
from app.services.schedule_service import ScheduleService


# Перевіряє, що normalize recurrence покриває fallback і валідацію recurring-правил.
def test_schedule_service_normalize_recurrence_and_weekdays():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    fallback_series = SimpleNamespace(
        frequency=RecurrenceFrequency.MONTHLY,
        interval=2,
        by_weekday=None,
        count=None,
        until=start_time + timedelta(days=60),
        start_time=start_time,
    )

    fallback = service._normalize_recurrence(None, start_time, fallback_series=fallback_series)
    assert fallback.frequency == RecurrenceFrequency.MONTHLY
    assert fallback.interval == 2
    assert fallback.by_weekday == [RecurrenceWeekday.MO]

    weekly_without_days = ScheduleRecurrence.model_construct(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday=[],
        count=None,
        until=None,
    )
    normalized = service._normalize_recurrence(weekly_without_days, start_time)
    assert normalized.by_weekday == [RecurrenceWeekday.MO]

    assert service._series_weekdays(SimpleNamespace(by_weekday="MO,WE", start_time=start_time)) == [
        RecurrenceWeekday.MO,
        RecurrenceWeekday.WE,
    ]
    assert service._series_weekdays(SimpleNamespace(by_weekday=None, start_time=start_time)) == [
        RecurrenceWeekday.MO,
    ]

    with pytest.raises(HTTPException) as no_rule_error:
        service._normalize_recurrence(None, start_time)
    assert no_rule_error.value.detail == "Для серії потрібне recurrence-правило"

    with pytest.raises(HTTPException) as invalid_until_error:
        service._normalize_recurrence(
            ScheduleRecurrence(
                frequency=RecurrenceFrequency.DAILY,
                until=start_time,
            ),
            start_time,
        )
    assert invalid_until_error.value.detail == "Дата завершення recurring-серії має бути пізніше за перше заняття"


# Перевіряє anchor-обчислення, materialization window і оновлення значень occurrence.
def test_schedule_service_anchor_and_update_helpers():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    end_time = start_time + timedelta(hours=1)
    workout_class = SimpleNamespace(
        start_time=start_time,
        end_time=end_time,
        extra_price=Decimal("15.00"),
        source_occurrence_start=None,
        title="  Old Title  ",
        capacity=8,
    )
    series = SimpleNamespace(
        start_time=start_time,
        end_time=end_time,
        extra_price=Decimal("20.00"),
        until=start_time + timedelta(days=7),
    )

    next_start, next_end = service._derive_following_anchor(
        workout_class,
        ScheduleUpdate(startTime=start_time + timedelta(hours=2)),
    )
    assert next_start == start_time + timedelta(hours=2)
    assert next_end == end_time + timedelta(hours=2)

    shifted_start, shifted_end = service._derive_series_anchor(
        series,
        workout_class,
        ScheduleUpdate(
            startTime=start_time + timedelta(hours=1),
            endTime=end_time + timedelta(hours=2),
        ),
    )
    assert shifted_start == start_time + timedelta(hours=1)
    assert shifted_end == start_time + timedelta(hours=3)

    untouched_start, untouched_end = service._derive_series_anchor(series, workout_class, ScheduleUpdate())
    assert untouched_start == start_time
    assert untouched_end == end_time

    assert ScheduleService._resolve_extra_price(ScheduleUpdate(isPaidExtra=False), series) is None
    assert ScheduleService._resolve_extra_price(
        ScheduleUpdate(extraPrice=Decimal("33.00")),
        series,
    ) == Decimal("33.00")
    assert ScheduleService._resolve_extra_price(ScheduleUpdate(), series) == Decimal("20.00")
    assert ScheduleService._source_occurrence_start(workout_class) == start_time
    assert ScheduleService._materialization_window_end(SimpleNamespace(until=None)) > datetime.now(UTC)
    assert ScheduleService._materialization_window_end(SimpleNamespace(until=start_time)) == start_time

    service._apply_occurrence_updates(
        workout_class,
        {
            "title": "  New Title  ",
            "start_time": start_time + timedelta(hours=1),
            "end_time": end_time + timedelta(hours=1),
            "capacity": 12,
        },
    )
    assert workout_class.title == "New Title"
    assert workout_class.start_time == start_time + timedelta(hours=1)
    assert workout_class.end_time == end_time + timedelta(hours=1)
    assert workout_class.capacity == 12


# Перевіряє доступи, бронювання і базові бізнес-обмеження helper-методів.
def test_schedule_service_access_and_validation_helpers():
    service = ScheduleService(AsyncMock())
    workout_class = SimpleNamespace(
        trainer_id="trainer-1",
        bookings=[SimpleNamespace(status=BookingStatus.CONFIRMED)],
    )
    valid_start = datetime(2026, 3, 30, 7, 0, tzinfo=UTC)
    valid_end = valid_start + timedelta(hours=1)

    ScheduleService._ensure_update_access(workout_class, SimpleNamespace(role=UserRole.ADMIN, id="admin"))
    ScheduleService._ensure_update_access(workout_class, SimpleNamespace(role=UserRole.TRAINER, id="trainer-1"))
    ScheduleService._ensure_delete_access(SimpleNamespace(role=UserRole.OWNER))
    ScheduleService._validate_time_range(valid_start, valid_end)
    ScheduleService._validate_pricing(False, None)

    assert service._has_confirmed_bookings(workout_class) is True

    with pytest.raises(HTTPException) as update_error:
        ScheduleService._ensure_update_access(
            workout_class,
            SimpleNamespace(role=UserRole.TRAINER, id="other"),
        )
    assert update_error.value.status_code == 403

    with pytest.raises(HTTPException) as delete_error:
        ScheduleService._ensure_delete_access(SimpleNamespace(role=UserRole.TRAINER))
    assert delete_error.value.status_code == 403

    with pytest.raises(HTTPException) as booking_error:
        service._ensure_occurrence_is_unbooked(workout_class)
    assert booking_error.value.detail == "Не можна видалити заняття, поки в ньому є підтверджені записи"

    with pytest.raises(HTTPException) as range_error:
        ScheduleService._validate_time_range(valid_end, valid_start)
    assert range_error.value.detail == "Час завершення має бути пізніше за час початку"

    with pytest.raises(HTTPException) as hours_error:
        ScheduleService._validate_time_range(
            datetime(2026, 3, 30, 20, 0, tzinfo=UTC),
            datetime(2026, 3, 30, 21, 0, tzinfo=UTC),
        )
    assert hours_error.value.detail == "Заняття можна планувати лише в межах роботи клубу: 06:00-22:00"

    with pytest.raises(HTTPException) as pricing_error:
        ScheduleService._validate_pricing(True, None)
    assert pricing_error.value.detail == "Для платного заняття потрібно вказати додаткову вартість"


# Перевіряє, що require series коректно реагує на відсутність series id або серії в БД.
@pytest.mark.asyncio
async def test_schedule_service_require_series_errors():
    service = ScheduleService(AsyncMock())
    service.series_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as missing_series_id:
        await service._require_series(SimpleNamespace(series_id=None))
    assert missing_series_id.value.detail == "Заняття не належить до серії"

    with pytest.raises(HTTPException) as missing_series:
        await service._require_series(SimpleNamespace(series_id="series-1"))
    assert missing_series.value.detail == "Recurring-серію не знайдено"


# Перевіряє fallback-гілку update series, коли нові occurrences не були materialized.
@pytest.mark.asyncio
async def test_update_series_returns_refreshed_occurrence_when_no_new_occurrences():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    workout_class = SimpleNamespace(
        id="class-1",
        title="Old Title",
        description=None,
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        source_occurrence_start=None,
    )
    series = SimpleNamespace(
        id="series-1",
        title="Old Title",
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="MO",
        count=3,
        until=None,
        rule_text="old-rule",
    )
    refreshed = SimpleNamespace(id="class-1", title="Updated Title")

    service._require_series = AsyncMock(return_value=series)
    service._ensure_scope_has_no_booked_occurrences = AsyncMock()
    service.series_repository.list_occurrences = AsyncMock(return_value=[])
    service.repository.delete = AsyncMock()
    service._clear_exclusions = AsyncMock()
    service._materialize_series_occurrences = AsyncMock(return_value=[])
    service.repository.get_by_id = AsyncMock(return_value=refreshed)

    result = await service._update_series(
        workout_class,
        ScheduleUpdate(title=" Updated Title ", scope=RecurrenceScope.SERIES),
    )

    assert result is refreshed
    service.repository.get_by_id.assert_awaited_once_with("class-1")


# Перевіряє, що update following повертає помилку, якщо split-серія не згенерувала нових occurrences.
@pytest.mark.asyncio
async def test_update_following_raises_when_new_series_generates_no_occurrences():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    workout_class = SimpleNamespace(
        id="class-1",
        title="Old Title",
        description=None,
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        source_occurrence_start=None,
    )
    series = SimpleNamespace(
        id="series-1",
        title="Old Title",
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="MO",
        count=3,
        until=None,
        rule_text="old-rule",
        exclusions=[],
    )

    service._require_series = AsyncMock(return_value=series)
    service._ensure_scope_has_no_booked_occurrences = AsyncMock()
    service.series_repository.list_occurrences = AsyncMock(return_value=[])
    service.repository.delete = AsyncMock()
    service._clear_exclusions = AsyncMock()
    service.series_repository.create = AsyncMock()
    service._materialize_series_occurrences = AsyncMock(return_value=[])

    with pytest.raises(HTTPException) as error:
        await service._update_following(
            workout_class,
            ScheduleUpdate(
                title="Split Series",
                scope=RecurrenceScope.FOLLOWING,
                recurrence=ScheduleRecurrence(
                    frequency=RecurrenceFrequency.WEEKLY,
                    byWeekday=[RecurrenceWeekday.MO],
                    count=2,
                ),
            ),
        )

    assert error.value.detail == "Нова серія не згенерувала занять"


# Перевіряє, що update series кидає помилку, якщо немає ні нових occurrences, ні fallback-обʼєкта.
@pytest.mark.asyncio
async def test_update_series_raises_when_no_occurrence_can_be_returned():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    workout_class = SimpleNamespace(
        id="class-1",
        title="Old Title",
        description=None,
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
    )
    series = SimpleNamespace(
        id="series-1",
        title="Old Title",
        trainer_id="trainer-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=8,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="MO",
        count=3,
        until=None,
        rule_text="old-rule",
    )

    service._require_series = AsyncMock(return_value=series)
    service._ensure_scope_has_no_booked_occurrences = AsyncMock()
    service.series_repository.list_occurrences = AsyncMock(return_value=[])
    service.repository.delete = AsyncMock()
    service._clear_exclusions = AsyncMock()
    service._materialize_series_occurrences = AsyncMock(return_value=[])
    service.repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as error:
        await service._update_series(
            workout_class,
            ScheduleUpdate(title="Updated Title", scope=RecurrenceScope.SERIES),
        )

    assert error.value.detail == "Після оновлення серія не містить жодної майбутньої occurrence"


# Перевіряє started-branch delete series, яка truncate-ить правило замість повного delete.
@pytest.mark.asyncio
async def test_delete_series_truncates_started_series():
    session = SimpleNamespace(delete=AsyncMock())
    service = ScheduleService(session)
    now = datetime.now(UTC)
    workout_class = SimpleNamespace(series_id="series-1")
    series = SimpleNamespace(
        id="series-1",
        start_time=now - timedelta(days=7),
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="MO",
        count=4,
        until=None,
        rule_text="old-rule",
    )

    service._require_series = AsyncMock(return_value=series)
    service._ensure_scope_has_no_booked_occurrences = AsyncMock()
    service.series_repository.list_occurrences = AsyncMock(return_value=[])
    service.repository.delete = AsyncMock()
    service._clear_exclusions = AsyncMock()

    await service._delete_series(workout_class)

    assert series.until is not None
    session.delete.assert_not_awaited()


# Перевіряє, що materialization повертає порожній список для вже закритого вікна.
@pytest.mark.asyncio
async def test_materialize_series_occurrences_returns_empty_when_window_is_closed():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)

    result = await service._materialize_series_occurrences(
        SimpleNamespace(
            id="series-1",
            start_time=start_time,
            end_time=start_time + timedelta(hours=1),
            until=start_time - timedelta(days=1),
            exclusions=[],
        ),
        start_boundary=start_time + timedelta(days=2),
    )

    assert result == []


# Перевіряє, що clear exclusions видаляє лише винятки від заданої дати й далі.
@pytest.mark.asyncio
async def test_clear_exclusions_removes_only_future_entries():
    service = ScheduleService(AsyncMock())
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    keep_exclusion = SimpleNamespace(occurrence_start=start_time - timedelta(days=7))
    remove_exclusion = SimpleNamespace(occurrence_start=start_time + timedelta(days=7))
    series = SimpleNamespace(exclusions=[keep_exclusion, remove_exclusion])
    service.series_repository.delete_exclusion = AsyncMock()

    await service._clear_exclusions(series, start_time)

    assert series.exclusions == [keep_exclusion]
    service.series_repository.delete_exclusion.assert_awaited_once_with(remove_exclusion)
