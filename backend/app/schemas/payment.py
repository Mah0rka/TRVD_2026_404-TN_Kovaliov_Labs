# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.api.docs import PAYMENT_CREATE_EXAMPLE, PAYMENT_EXAMPLE
from app.schemas.user import UserRead


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": PAYMENT_CREATE_EXAMPLE})

    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=3, max_length=32)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": PAYMENT_EXAMPLE})

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
