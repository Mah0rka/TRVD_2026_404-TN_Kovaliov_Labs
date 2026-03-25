# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus
from app.schemas.schedule import TrainerSummary


class BookingClassSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    trainer_id: str
    start_time: datetime
    end_time: datetime
    capacity: int
    is_paid_extra: bool
    extra_price: Decimal | None
    trainer: TrainerSummary


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    class_id: str
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    workout_class: BookingClassSummary
