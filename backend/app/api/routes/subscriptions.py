# Коротко: маршрут обробляє HTTP-запити для модуля абонементів.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, rate_limit, require_roles
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.membership_plan import MembershipPlanCreate, MembershipPlanRead, MembershipPlanUpdate
from app.schemas.subscription import (
    SubscriptionFreezeRequest,
    SubscriptionManagementIssueRequest,
    SubscriptionManagementUpdate,
    SubscriptionPurchaseRequest,
    SubscriptionRead,
)
from app.services.membership_plan_service import MembershipPlanService
from app.services.subscription_service import SubscriptionService

router = APIRouter()


@router.get("/plans", response_model=list[MembershipPlanRead])
async def list_membership_plans(
    current_user: User = Depends(require_roles(UserRole.CLIENT, UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[MembershipPlanRead]:
    service = MembershipPlanService(db)
    plans = await service.list_plans(
        active_only=current_user.role == UserRole.CLIENT,
        public_only=current_user.role == UserRole.CLIENT,
    )
    return [MembershipPlanRead.model_validate(item) for item in plans]


@router.post("/plans", response_model=MembershipPlanRead)
async def create_membership_plan(
    payload: MembershipPlanCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    service = MembershipPlanService(db)
    plan = await service.create_plan(payload)
    return MembershipPlanRead.model_validate(plan)


@router.patch("/plans/{plan_id}", response_model=MembershipPlanRead)
async def update_membership_plan(
    plan_id: str,
    payload: MembershipPlanUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    service = MembershipPlanService(db)
    plan = await service.update_plan(plan_id, payload)
    return MembershipPlanRead.model_validate(plan)


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_membership_plan(
    plan_id: str,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = MembershipPlanService(db)
    await service.delete_plan(plan_id)


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
    subscription = await service.purchase(
        current_user.id,
        subscription_type=payload.type,
        plan_id=payload.plan_id,
    )
    return SubscriptionRead.model_validate(subscription)


@router.get("", response_model=list[SubscriptionRead])
async def all_subscriptions(
    user_id: str | None = None,
    include_deleted: bool = False,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[SubscriptionRead]:
    service = SubscriptionService(db)
    subscriptions = await service.list_for_management(user_id=user_id, include_deleted=include_deleted)
    return [SubscriptionRead.model_validate(item) for item in subscriptions]


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_client_subscription(
    subscription_id: str,
    payload: SubscriptionManagementUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.update_for_management(current_user.id, subscription_id, payload)
    return SubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=204)
async def delete_client_subscription(
    subscription_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = SubscriptionService(db)
    await service.delete_for_management(current_user.id, subscription_id)


@router.post("/issue", response_model=SubscriptionRead)
async def issue_client_subscription(
    payload: SubscriptionManagementIssueRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.issue_for_management(current_user.id, payload)
    return SubscriptionRead.model_validate(subscription)


@router.post("/{subscription_id}/restore", response_model=SubscriptionRead)
async def restore_client_subscription(
    subscription_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.restore_for_management(current_user.id, subscription_id)
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
