# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.api.docs import (
    MEMBERSHIP_PLAN_CREATE_EXAMPLE,
    MEMBERSHIP_PLAN_EXAMPLE,
    MEMBERSHIP_PLAN_UPDATE_EXAMPLE,
)
from app.models.subscription import SubscriptionType


class MembershipPlanCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": MEMBERSHIP_PLAN_CREATE_EXAMPLE})

    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    type: SubscriptionType
    duration_days: int = Field(ge=1, le=3660)
    visits_limit: int | None = Field(default=None, ge=1, le=1000)
    price: Decimal = Field(gt=0)
    currency: str = Field(default="UAH", min_length=3, max_length=8)
    sort_order: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True
    is_public: bool = True


class MembershipPlanUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": MEMBERSHIP_PLAN_UPDATE_EXAMPLE})

    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    type: SubscriptionType | None = None
    duration_days: int | None = Field(default=None, ge=1, le=3660)
    visits_limit: int | None = Field(default=None, ge=1, le=1000)
    price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    is_active: bool | None = None
    is_public: bool | None = None


class MembershipPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": MEMBERSHIP_PLAN_EXAMPLE})

    id: str
    title: str
    description: str | None
    type: SubscriptionType
    duration_days: int
    visits_limit: int | None
    price: Decimal
    currency: str
    sort_order: int
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
