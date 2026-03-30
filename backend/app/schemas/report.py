# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.docs import REVENUE_REPORT_EXAMPLE, TRAINER_POPULARITY_EXAMPLE


class RevenueReport(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": REVENUE_REPORT_EXAMPLE})

    period: dict[str, datetime]
    total_revenue: float
    transactions_count: int
    currency: str


class TrainerPopularityReport(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": TRAINER_POPULARITY_EXAMPLE})

    trainer_id: str
    name: str
    total_attendees: int
    classes_taught: int
    average_attendees_per_class: float
