from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, rate_limit, require_roles
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.subscription import (
    SubscriptionFreezeRequest,
    SubscriptionPurchaseRequest,
    SubscriptionRead,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.post("/purchase", response_model=SubscriptionRead)
async def purchase_subscription(
    payload: SubscriptionPurchaseRequest,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    _: None = Depends(
        rate_limit(
            "subscriptions:purchase",
            settings.subscription_purchase_rate_limit,
            settings.auth_rate_limit_window_seconds,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.purchase(current_user.id, payload.type)
    return SubscriptionRead.model_validate(subscription)


@router.patch("/{subscription_id}/freeze", response_model=SubscriptionRead)
async def freeze_subscription(
    subscription_id: str,
    payload: SubscriptionFreezeRequest,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    _: None = Depends(
        rate_limit(
            "subscriptions:freeze",
            settings.subscription_freeze_rate_limit,
            settings.auth_rate_limit_window_seconds,
        )
    ),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.freeze(current_user.id, subscription_id, payload.days)
    return SubscriptionRead.model_validate(subscription)


@router.get("/my-subscriptions", response_model=list[SubscriptionRead])
async def my_subscriptions(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[SubscriptionRead]:
    service = SubscriptionService(db)
    subscriptions = await service.list_for_user(current_user.id)
    return [SubscriptionRead.model_validate(item) for item in subscriptions]
