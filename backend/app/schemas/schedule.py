# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus
from app.models.workout_class import WorkoutType


class ScheduleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    type: WorkoutType
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    capacity: int = Field(ge=1, le=100)
    trainer_id: str | None = Field(default=None, alias="trainerId")
    is_paid_extra: bool = Field(default=False, alias="isPaidExtra")
    extra_price: Decimal | None = Field(default=None, alias="extraPrice")


class ScheduleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    type: WorkoutType | None = None
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    capacity: int | None = Field(default=None, ge=1, le=100)
    trainer_id: str | None = Field(default=None, alias="trainerId")
    is_paid_extra: bool | None = Field(default=None, alias="isPaidExtra")
    extra_price: Decimal | None = Field(default=None, alias="extraPrice")


class TrainerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str


class ScheduleCompleteRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class BookingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: BookingStatus


class AttendeeUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str
    last_name: str


class ScheduleAttendeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: BookingStatus
    created_at: datetime
    user: AttendeeUserSummary


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    trainer: TrainerSummary
    completed_at: datetime | None = None
    completion_comment: str | None = None
    completed_by: TrainerSummary | None = None
    bookings: list[BookingSummary] = []
    created_at: datetime
    updated_at: datetime
