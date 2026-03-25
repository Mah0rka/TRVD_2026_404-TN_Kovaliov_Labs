# Схеми задають валідацію вхідних даних і формат відповідей API.

from pydantic import BaseModel


class ClubStats(BaseModel):
    clients_count: int
    trainers_count: int
    classes_next_7_days: int
    active_subscriptions_count: int
