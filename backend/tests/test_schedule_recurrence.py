# Тести перевіряють helper-логіку recurring-правил розкладу.

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.models.workout_series import RecurrenceFrequency
from app.schemas.schedule import RecurrenceWeekday, ScheduleRecurrence
from app.services.schedule_recurrence import (
    build_recurrence_summary,
    ensure_aware,
    generate_occurrence_starts,
    recurrence_to_read,
    serialize_recurrence_rule,
    weekday_codes_for_start,
)


# Перевіряє, що ensure aware нормалізує naive і aware datetime до UTC.
def test_ensure_aware_normalizes_datetimes():
    naive_value = datetime(2026, 4, 1, 9, 0)
    aware_value = datetime(2026, 4, 1, 12, 0, tzinfo=ZoneInfo("Europe/Kiev"))

    normalized_naive = ensure_aware(naive_value)
    normalized_aware = ensure_aware(aware_value)

    assert normalized_naive.tzinfo == UTC
    assert normalized_aware.tzinfo == UTC
    assert normalized_aware.hour == 9


# Перевіряє, що weekday code визначається від дати старту occurrence.
def test_weekday_codes_for_start_returns_expected_code():
    monday = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)

    assert weekday_codes_for_start(monday) == ["MO"]


# Перевіряє, що RRULE серіалізується з until і генерує всі occurrences без вікна.
def test_serialize_recurrence_rule_with_until_and_generate_all_occurrences():
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    recurrence = ScheduleRecurrence(
        frequency=RecurrenceFrequency.DAILY,
        interval=2,
        until=start_time + timedelta(days=4),
    )

    rule_text = serialize_recurrence_rule(start_time, recurrence)
    generated = generate_occurrence_starts(start_time=start_time, rule_text=rule_text)

    assert "UNTIL=20260403T090000Z" in rule_text
    assert [item.date().isoformat() for item in generated] == [
        "2026-03-30",
        "2026-04-01",
        "2026-04-03",
    ]


# Перевіряє, що генерація occurrences поважає вікно фільтрації.
def test_generate_occurrence_starts_respects_window_boundaries():
    start_time = datetime(2026, 3, 30, 9, 0, tzinfo=UTC)
    recurrence = ScheduleRecurrence(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        byWeekday=[RecurrenceWeekday.MO],
        count=4,
    )
    rule_text = serialize_recurrence_rule(start_time, recurrence)

    generated = generate_occurrence_starts(
        start_time=start_time,
        rule_text=rule_text,
        window_start=start_time + timedelta(days=7),
        window_end=start_time + timedelta(days=14),
    )

    assert [item.date().isoformat() for item in generated] == [
        "2026-04-06",
        "2026-04-13",
    ]


# Перевіряє, що recurrence read-model повертає summary і weekday-перелік.
def test_recurrence_to_read_maps_series_to_api_model():
    series = SimpleNamespace(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="MO,WE",
        count=4,
        until=None,
    )

    result = recurrence_to_read(series)

    assert result.by_weekday == [RecurrenceWeekday.MO, RecurrenceWeekday.WE]
    assert result.summary == "Щотижня (MO,WE), 4 занять"


# Перевіряє різні варіанти summary для recurring-серій.
def test_build_recurrence_summary_covers_interval_until_and_open_end():
    every_second_month = SimpleNamespace(
        frequency=RecurrenceFrequency.MONTHLY,
        interval=2,
        by_weekday=None,
        count=None,
        until=datetime(2026, 6, 1, 9, 0),
    )
    open_ended = SimpleNamespace(
        frequency=RecurrenceFrequency.DAILY,
        interval=1,
        by_weekday=None,
        count=None,
        until=None,
    )

    assert build_recurrence_summary(every_second_month) == "Щомісяця кожні 2 до 01.06.2026"
    assert build_recurrence_summary(open_ended) == "Щодня, без фіксованого завершення"
