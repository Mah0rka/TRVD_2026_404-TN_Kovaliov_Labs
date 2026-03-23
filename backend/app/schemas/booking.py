from datetime import datetime

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
