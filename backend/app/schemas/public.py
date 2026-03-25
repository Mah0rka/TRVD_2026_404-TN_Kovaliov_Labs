# Коротко: схеми описують DTO та валідацію для модуля публічних даних.

from pydantic import BaseModel


class ClubStats(BaseModel):
    clients_count: int
    trainers_count: int
    classes_next_7_days: int
    active_subscriptions_count: int
