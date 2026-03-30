# Схеми задають валідацію вхідних даних і формат відповідей API.

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.docs import (
    SUBSCRIPTION_EXAMPLE,
    SUBSCRIPTION_FREEZE_EXAMPLE,
    SUBSCRIPTION_ISSUE_EXAMPLE,
    SUBSCRIPTION_MANAGEMENT_UPDATE_EXAMPLE,
    SUBSCRIPTION_PURCHASE_EXAMPLE,
)
from app.models.subscription import SubscriptionStatus, SubscriptionType
from app.schemas.membership_plan import MembershipPlanRead
from app.schemas.user import UserRead


class SubscriptionPurchaseRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SUBSCRIPTION_PURCHASE_EXAMPLE})

    plan_id: str | None = None
    type: SubscriptionType | None = None


class SubscriptionFreezeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SUBSCRIPTION_FREEZE_EXAMPLE})

    days: int = Field(ge=7, le=30)


class SubscriptionManagementUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SUBSCRIPTION_MANAGEMENT_UPDATE_EXAMPLE})

    plan_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: SubscriptionStatus | None = None
    total_visits: int | None = Field(default=None, ge=0, le=1000)
    remaining_visits: int | None = Field(default=None, ge=0, le=1000)


class SubscriptionManagementIssueRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": SUBSCRIPTION_ISSUE_EXAMPLE})

    user_id: str
    plan_id: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    total_visits: int | None = Field(default=None, ge=0, le=1000)
    remaining_visits: int | None = Field(default=None, ge=0, le=1000)


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": SUBSCRIPTION_EXAMPLE})

    id: str
    user_id: str
    plan_id: str | None
    type: SubscriptionType
    start_date: datetime
    end_date: datetime
    status: SubscriptionStatus
    total_visits: int | None
    remaining_visits: int | None
    user: UserRead | None = None
    plan: MembershipPlanRead | None = None
    last_modified_by: UserRead | None = None
    last_modified_at: datetime | None = None
    deleted_by: UserRead | None = None
    deleted_at: datetime | None = None
    restored_by: UserRead | None = None
    restored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
