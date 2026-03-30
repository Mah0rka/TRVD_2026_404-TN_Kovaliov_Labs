# Модуль містить допоміжну логіку для recurring-правил розкладу.

from datetime import UTC, datetime

from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU, rrulestr

from app.models.workout_series import RecurrenceFrequency, WorkoutSeries
from app.schemas.schedule import RecurrenceWeekday, ScheduleRecurrence, ScheduleRecurrenceRead

# Відображає weekday-коди API у обʼєкти python-dateutil для RRULE.
WEEKDAY_TO_RULE = {
    RecurrenceWeekday.MO.value: MO,
    RecurrenceWeekday.TU.value: TU,
    RecurrenceWeekday.WE.value: WE,
    RecurrenceWeekday.TH.value: TH,
    RecurrenceWeekday.FR.value: FR,
    RecurrenceWeekday.SA.value: SA,
    RecurrenceWeekday.SU.value: SU,
}

# Людяні підписи частот для коротких описів recurring-правил.
FREQUENCY_LABELS = {
    RecurrenceFrequency.DAILY: "Щодня",
    RecurrenceFrequency.WEEKLY: "Щотижня",
    RecurrenceFrequency.MONTHLY: "Щомісяця",
}


# Нормалізує datetime до timezone-aware UTC-представлення.
def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


# Повертає weekday-код для дати старту першої occurrence.
def weekday_codes_for_start(start_time: datetime) -> list[str]:
    codes = list(WEEKDAY_TO_RULE)
    return [codes[start_time.weekday()]]


# Серіалізує recurrence DTO у текстове RRULE-представлення для зберігання.
def serialize_recurrence_rule(start_time: datetime, recurrence: ScheduleRecurrence) -> str:
    parts = [f"FREQ={recurrence.frequency.value}", f"INTERVAL={recurrence.interval}"]
    if recurrence.by_weekday:
        parts.append(f"BYDAY={','.join(day.value for day in recurrence.by_weekday)}")
    if recurrence.count is not None:
        parts.append(f"COUNT={recurrence.count}")
    if recurrence.until is not None:
        until = ensure_aware(recurrence.until).strftime("%Y%m%dT%H%M%SZ")
        parts.append(f"UNTIL={until}")
    dtstart = ensure_aware(start_time).strftime("%Y%m%dT%H%M%SZ")
    return f"DTSTART:{dtstart}\nRRULE:{';'.join(parts)}"


# Генерує дати occurrences для RRULE в межах заданого вікна.
def generate_occurrence_starts(
    *,
    start_time: datetime,
    rule_text: str,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> list[datetime]:
    rule = rrulestr(rule_text, dtstart=ensure_aware(start_time))
    if window_start is None and window_end is None:
        return list(rule)
    return list(
        rule.between(
            ensure_aware(window_start or start_time),
            ensure_aware(window_end or start_time),
            inc=True,
        )
    )


# Перетворює модель recurring-серії у DTO для відповіді API.
def recurrence_to_read(series: WorkoutSeries) -> ScheduleRecurrenceRead:
    weekday_codes = [RecurrenceWeekday(value) for value in (series.by_weekday or "").split(",") if value]
    return ScheduleRecurrenceRead(
        frequency=series.frequency,
        interval=series.interval,
        byWeekday=weekday_codes,
        count=series.count,
        until=series.until,
        summary=build_recurrence_summary(series),
    )


# Будує короткий текстовий опис recurring-правила для UI та API-відповідей.
def build_recurrence_summary(series: WorkoutSeries) -> str:
    base = FREQUENCY_LABELS[series.frequency]
    if series.interval > 1:
        base = f"{base} кожні {series.interval}"
    if series.frequency == RecurrenceFrequency.WEEKLY and series.by_weekday:
        base = f"{base} ({series.by_weekday})"
    if series.count:
        return f"{base}, {series.count} занять"
    if series.until:
        return f"{base} до {ensure_aware(series.until).strftime('%d.%m.%Y')}"
    return f"{base}, без фіксованого завершення"
