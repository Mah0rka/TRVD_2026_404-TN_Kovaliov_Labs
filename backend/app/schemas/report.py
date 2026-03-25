# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime

from pydantic import BaseModel


class RevenueReport(BaseModel):
    period: dict[str, datetime]
    total_revenue: float
    transactions_count: int
    currency: str


class TrainerPopularityReport(BaseModel):
    trainer_id: str
    name: str
    total_attendees: int
    classes_taught: int
    average_attendees_per_class: float
