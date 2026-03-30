# Схеми задають валідацію вхідних даних і формат відповідей API.

from pydantic import BaseModel, ConfigDict

from app.api.docs import CLUB_STATS_EXAMPLE


class ClubStats(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": CLUB_STATS_EXAMPLE})

    clients_count: int
    trainers_count: int
    classes_next_7_days: int
    active_subscriptions_count: int
