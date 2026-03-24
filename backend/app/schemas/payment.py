from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=3, max_length=32)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    amount: Decimal
    currency: str
    status: str
    method: str
    purpose: str
    description: str | None = None
    booking_class_id: str | None = None
    user: UserRead | None = None
    created_at: datetime
    updated_at: datetime
