from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import SubscriptionStatus, SubscriptionType


class SubscriptionPurchaseRequest(BaseModel):
    type: SubscriptionType


class SubscriptionFreezeRequest(BaseModel):
    days: int = Field(ge=7, le=30)


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: SubscriptionType
    start_date: datetime
    end_date: datetime
    status: SubscriptionStatus
    total_visits: int | None
    remaining_visits: int | None
    created_at: datetime
    updated_at: datetime
