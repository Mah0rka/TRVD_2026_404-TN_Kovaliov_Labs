# Тести перевіряють валідацію recurring-схем розкладу.

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.workout_series import RecurrenceFrequency
from app.schemas.schedule import RecurrenceWeekday, ScheduleRecurrence, ScheduleRecurrenceRead


# Перевіряє, що recurrence не приймає count і until одночасно.
def test_schedule_recurrence_rejects_count_and_until_together():
    with pytest.raises(ValidationError) as error:
        ScheduleRecurrence(
            frequency=RecurrenceFrequency.DAILY,
            count=5,
            until=datetime(2026, 4, 1, 9, 0),
        )

    assert "Можна вказати або count, або until" in str(error.value)


# Перевіряє, що weekly recurrence вимагає хоча б один день тижня.
def test_schedule_recurrence_rejects_weekly_rule_without_weekdays():
    with pytest.raises(ValidationError) as error:
        ScheduleRecurrence(
            frequency=RecurrenceFrequency.WEEKLY,
        )

    assert "Для тижневого повторення потрібен хоча б один день тижня" in str(error.value)


# Перевіряє, що read-модель нормалізує naive until у timezone-aware формат.
def test_schedule_recurrence_read_normalizes_naive_until():
    result = ScheduleRecurrenceRead(
        frequency=RecurrenceFrequency.WEEKLY,
        byWeekday=[RecurrenceWeekday.MO],
        until=datetime(2026, 4, 1, 9, 0),
        summary="Щотижня до 01.04.2026",
    )

    assert result.until is not None
    assert result.until.tzinfo is not None
