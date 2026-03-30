# Схеми задають валідацію вхідних даних і формат відповідей API.

import enum

from datetime import UTC, datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.docs import (
    ATTENDEE_USER_EXAMPLE,
    BOOKING_SUMMARY_EXAMPLE,
    SCHEDULE_ATTENDEE_EXAMPLE,
    SCHEDULE_COMPLETE_EXAMPLE,
    SCHEDULE_CREATE_EXAMPLE,
    SCHEDULE_EXAMPLE,
    SCHEDULE_RECURRENCE_EXAMPLE,
    SCHEDULE_RECURRENCE_READ_EXAMPLE,
    SCHEDULE_UPDATE_EXAMPLE,
    TRAINER_EXAMPLE,
)
from app.models.booking import BookingStatus
from app.models.workout_class import WorkoutType
from app.models.workout_series import RecurrenceFrequency


# Описує scope, до якого застосовується зміна recurring-розкладу.
class RecurrenceScope(str, enum.Enum):
    OCCURRENCE = "OCCURRENCE"
    FOLLOWING = "FOLLOWING"
    SERIES = "SERIES"


# Перелічує дні тижня для weekly-recurring правил.
class RecurrenceWeekday(str, enum.Enum):
    MO = "MO"
    TU = "TU"
    WE = "WE"
    TH = "TH"
    FR = "FR"
    SA = "SA"
    SU = "SU"


# Валідує recurrence-правило, яке надходить у create/update schedule.
class ScheduleRecurrence(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SCHEDULE_RECURRENCE_EXAMPLE})

    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1, le=52)
    by_weekday: list[RecurrenceWeekday] = Field(default_factory=list, alias="byWeekday")
    count: int | None = Field(default=None, ge=1, le=365)
    until: datetime | None = None

    # Забороняє взаємовиключні ліміти recurring-правила.
    @model_validator(mode="after")
    def validate_limits(self) -> "ScheduleRecurrence":
        if self.count is not None and self.until is not None:
            raise ValueError("Можна вказати або count, або until")
        if self.frequency == RecurrenceFrequency.WEEKLY and not self.by_weekday:
            raise ValueError("Для тижневого повторення потрібен хоча б один день тижня")
        return self


# Повертає recurrence у форматі read-model разом із summary для UI.
class ScheduleRecurrenceRead(ScheduleRecurrence):
    model_config = ConfigDict(json_schema_extra={"example": SCHEDULE_RECURRENCE_READ_EXAMPLE})

    summary: str

    # Нормалізує until до aware-формату в serializable read-моделі.
    @model_validator(mode="after")
    def normalize_until(self) -> "ScheduleRecurrenceRead":
        if self.until and self.until.tzinfo is None:
            self.until = self.until.replace(tzinfo=UTC)
        return self


# Валідовує payload створення заняття або recurring-серії.
class ScheduleCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SCHEDULE_CREATE_EXAMPLE})

    title: str = Field(min_length=2, max_length=255)
    type: WorkoutType
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    capacity: int = Field(ge=1, le=100)
    trainer_id: str | None = Field(default=None, alias="trainerId")
    is_paid_extra: bool = Field(default=False, alias="isPaidExtra")
    extra_price: Decimal | None = Field(default=None, alias="extraPrice")
    recurrence: ScheduleRecurrence | None = None


# Підтримує patch-оновлення заняття, occurrence або цілої recurring-серії.
class ScheduleUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SCHEDULE_UPDATE_EXAMPLE})

    title: str | None = Field(default=None, min_length=2, max_length=255)
    type: WorkoutType | None = None
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    capacity: int | None = Field(default=None, ge=1, le=100)
    trainer_id: str | None = Field(default=None, alias="trainerId")
    is_paid_extra: bool | None = Field(default=None, alias="isPaidExtra")
    extra_price: Decimal | None = Field(default=None, alias="extraPrice")
    recurrence: ScheduleRecurrence | None = None
    scope: RecurrenceScope = RecurrenceScope.OCCURRENCE


# Повертає короткі дані тренера для schedule-відповідей.
class TrainerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": TRAINER_EXAMPLE})

    id: str
    first_name: str
    last_name: str


# Приймає службовий коментар до підтвердження завершення заняття.
class ScheduleCompleteRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SCHEDULE_COMPLETE_EXAMPLE})

    comment: str | None = Field(default=None, max_length=2000)


# Повертає скорочені дані бронювання у складі schedule-відповіді.
class BookingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": BOOKING_SUMMARY_EXAMPLE})

    id: str
    user_id: str
    status: BookingStatus


# Повертає короткі дані користувача в attendee-списку.
class AttendeeUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": ATTENDEE_USER_EXAMPLE})

    id: str
    email: str
    first_name: str
    last_name: str


# Повертає одного відвідувача заняття разом із користувацькими даними.
class ScheduleAttendeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": SCHEDULE_ATTENDEE_EXAMPLE})

    id: str
    user_id: str
    status: BookingStatus
    created_at: datetime
    user: AttendeeUserSummary


# Описує повну read-модель заняття, включно з recurring-метаданими.
class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": SCHEDULE_EXAMPLE})

    id: str
    title: str
    description: str | None
    trainer_id: str
    start_time: datetime
    end_time: datetime
    capacity: int
    type: WorkoutType
    is_paid_extra: bool
    extra_price: Decimal | None
    series_id: str | None = None
    source_occurrence_start: datetime | None = None
    is_series_exception: bool = False
    recurrence: ScheduleRecurrenceRead | None = None
    trainer: TrainerSummary
    completed_at: datetime | None = None
    completion_comment: str | None = None
    completed_by: TrainerSummary | None = None
    bookings: list[BookingSummary] = []
    created_at: datetime
    updated_at: datetime
