# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_REQUIRED_RESPONSE,
    MEMBERSHIP_PLAN_EXAMPLE,
    PERMISSION_DENIED_RESPONSE,
    RATE_LIMIT_RESPONSE,
    SUBSCRIPTION_EXAMPLE,
    VALIDATION_ERROR_RESPONSE,
    bad_request_response,
    conflict_response,
    merge_responses,
    no_content_response,
    not_found_response,
    response_example,
)
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


# Повертає список планів абонементів з урахуванням ролі доступу.
@router.get(
    "/plans",
    response_model=list[MembershipPlanRead],
    summary="Отримати список планів абонементів",
    description=(
        "Повертає доступні плани абонементів. Клієнти бачать лише активні та публічні плани, "
        "а адміністрація отримує повний каталог."
    ),
    responses=merge_responses(
        {200: response_example("Список планів абонементів.", [MEMBERSHIP_PLAN_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
    ),
)
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


# Створює новий план абонемента для адміністрації.
@router.post(
    "/plans",
    response_model=MembershipPlanRead,
    summary="Створити план абонемента",
    description="Створює новий тарифний план для адміністративного каталогу абонементів.",
    responses=merge_responses(
        {200: response_example("План абонемента успішно створено.", MEMBERSHIP_PLAN_EXAMPLE)},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def create_membership_plan(
    payload: MembershipPlanCreate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    service = MembershipPlanService(db)
    plan = await service.create_plan(payload)
    return MembershipPlanRead.model_validate(plan)


# Оновлює дані існуючого плану абонемента.
@router.patch(
    "/plans/{plan_id}",
    response_model=MembershipPlanRead,
    summary="Оновити план абонемента",
    description="Оновлює вибраний тарифний план без створення нового запису.",
    responses=merge_responses(
        {
            200: response_example(
                "План абонемента успішно оновлено.",
                {**MEMBERSHIP_PLAN_EXAMPLE, "price": 1190.0, "visits_limit": 16},
            )
        },
        not_found_response("План абонемента не знайдено.", "Membership plan not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def update_membership_plan(
    plan_id: Annotated[
        str,
        Path(
            description="Ідентифікатор плану абонемента, який треба змінити.",
            examples=["plan-monthly-12"],
        ),
    ],
    payload: MembershipPlanUpdate,
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    service = MembershipPlanService(db)
    plan = await service.update_plan(plan_id, payload)
    return MembershipPlanRead.model_validate(plan)


# Видаляє план абонемента, якщо це дозволено правилами.
@router.delete(
    "/plans/{plan_id}",
    status_code=204,
    summary="Видалити план абонемента",
    description=(
        "Видаляє тарифний план, якщо він ще не використовується в абонементах клієнтів."
    ),
    responses=merge_responses(
        {204: no_content_response("План абонемента успішно видалено.")},
        not_found_response("План абонемента не знайдено.", "Membership plan not found"),
        conflict_response(
            "План уже використовується в абонементах і не може бути видалений.",
            "Plan is already used in subscriptions and cannot be deleted",
        ),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def delete_membership_plan(
    plan_id: str = Path(
        description="Ідентифікатор плану абонемента, який треба видалити.",
        examples=["plan-monthly-12"],
    ),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = MembershipPlanService(db)
    await service.delete_plan(plan_id)


# Оформлює купівлю абонемента для поточного користувача.
@router.post(
    "/purchase",
    response_model=SubscriptionRead,
    summary="Купити абонемент",
    description=(
        "Оформлює покупку нового абонемента для поточного клієнта. Клієнт може вказати "
        "конкретний `plan_id` або тип абонемента, якщо система має відповідний публічний план."
    ),
    responses=merge_responses(
        {200: response_example("Абонемент успішно придбано й активовано.", SUBSCRIPTION_EXAMPLE)},
        bad_request_response(
            "План не передано або вхідні дані не відповідають правилам покупки.",
            "Membership plan is required",
        ),
        not_found_response("План абонемента не знайдено або він недоступний для покупки.", "Membership plan not found"),
        conflict_response(
            "У користувача вже є активний або заморожений абонемент.",
            "Finish or pause your current membership before purchasing a new one",
        ),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        RATE_LIMIT_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
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


# Повертає список абонементів для адміністративного перегляду.
@router.get(
    "",
    response_model=list[SubscriptionRead],
    summary="Отримати список абонементів",
    description=(
        "Адміністративний список абонементів із можливістю фільтрації за користувачем "
        "та включенням soft-deleted записів."
    ),
    responses=merge_responses(
        {200: response_example("Список абонементів для management-перегляду.", [SUBSCRIPTION_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def all_subscriptions(
    user_id: str | None = Query(
        default=None,
        description="Необов'язковий UUID користувача для відбору лише його абонементів.",
        examples=["user-7f6c4d4c"],
    ),
    include_deleted: bool = Query(
        default=False,
        description="Якщо `true`, у відповідь також потраплять soft-deleted абонементи.",
        examples=[False],
    ),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[SubscriptionRead]:
    service = SubscriptionService(db)
    subscriptions = await service.list_for_management(user_id=user_id, include_deleted=include_deleted)
    return [SubscriptionRead.model_validate(item) for item in subscriptions]


# Оновлює клієнтський абонемент у management-сценарії.
@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionRead,
    summary="Оновити абонемент у management-режимі",
    description=(
        "Дозволяє адміністрації змінювати терміни дії, статус, план або ліміти відвідувань "
        "для вибраного абонемента."
    ),
    responses=merge_responses(
        {
            200: response_example(
                "Абонемент успішно оновлено.",
                {**SUBSCRIPTION_EXAMPLE, "status": "FROZEN", "remaining_visits": 10},
            )
        },
        bad_request_response(
            "Стан або ліміти абонемента некоректні для збереження.",
            "Remaining visits cannot exceed total visits",
        ),
        not_found_response("Абонемент не знайдено.", "Subscription not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def update_client_subscription(
    subscription_id: Annotated[
        str,
        Path(
            description="Ідентифікатор абонемента, який треба змінити.",
            examples=["subscription-501"],
        ),
    ],
    payload: SubscriptionManagementUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.update_for_management(current_user.id, subscription_id, payload)
    return SubscriptionRead.model_validate(subscription)


# Позначає абонемент як видалений у management-сценарії.
@router.delete(
    "/{subscription_id}",
    status_code=204,
    summary="Видалити абонемент у management-режимі",
    description="Позначає абонемент як видалений, не стираючи історію повністю з бази даних.",
    responses=merge_responses(
        {204: no_content_response("Абонемент успішно позначено як видалений.")},
        bad_request_response("Абонемент уже видалено або не можна видалити повторно.", "Subscription already deleted"),
        not_found_response("Абонемент не знайдено.", "Subscription not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def delete_client_subscription(
    subscription_id: str = Path(
        description="Ідентифікатор абонемента, який треба видалити.",
        examples=["subscription-501"],
    ),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = SubscriptionService(db)
    await service.delete_for_management(current_user.id, subscription_id)


# Видає абонемент клієнту вручну від імені менеджера.
@router.post(
    "/issue",
    response_model=SubscriptionRead,
    summary="Видати абонемент клієнту вручну",
    description=(
        "Створює абонемент від імені менеджера або адміністратора без клієнтського checkout-сценарію."
    ),
    responses=merge_responses(
        {200: response_example("Абонемент успішно видано клієнту.", SUBSCRIPTION_EXAMPLE)},
        bad_request_response(
            "Параметри дат або ліміти відвідувань не пройшли валідацію бізнес-правил.",
            "Remaining visits cannot exceed total visits",
        ),
        not_found_response("Користувача або план абонемента не знайдено.", "User not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def issue_client_subscription(
    payload: SubscriptionManagementIssueRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.issue_for_management(current_user.id, payload)
    return SubscriptionRead.model_validate(subscription)


# Відновлює раніше видалений абонемент.
@router.post(
    "/{subscription_id}/restore",
    response_model=SubscriptionRead,
    summary="Відновити видалений абонемент",
    description=(
        "Скасовує soft-delete для абонемента. Якщо термін дії ще не вийшов, API може "
        "повернути його до статусу ACTIVE."
    ),
    responses=merge_responses(
        {200: response_example("Абонемент успішно відновлено.", SUBSCRIPTION_EXAMPLE)},
        bad_request_response("Абонемент не перебуває у стані deleted.", "Subscription is not deleted"),
        not_found_response("Абонемент не знайдено.", "Subscription not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def restore_client_subscription(
    subscription_id: str = Path(
        description="Ідентифікатор видаленого абонемента, який треба відновити.",
        examples=["subscription-501"],
    ),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionRead:
    service = SubscriptionService(db)
    subscription = await service.restore_for_management(current_user.id, subscription_id)
    return SubscriptionRead.model_validate(subscription)


# Ставить активний абонемент на паузу на вказаний строк.
@router.patch(
    "/{subscription_id}/freeze",
    response_model=SubscriptionRead,
    summary="Заморозити власний абонемент",
    description=(
        "Ставить активний абонемент клієнта на паузу на вказану кількість днів "
        "і продовжує дату завершення."
    ),
    responses=merge_responses(
        {200: response_example("Абонемент успішно заморожено.", {**SUBSCRIPTION_EXAMPLE, "status": "FROZEN"})},
        bad_request_response(
            "Заморозка доступна лише для активного абонемента та в допустимих межах.",
            "Only active subscriptions can be frozen",
        ),
        not_found_response("Абонемент не знайдено.", "Subscription not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        RATE_LIMIT_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def freeze_subscription(
    subscription_id: Annotated[
        str,
        Path(
            description="Ідентифікатор активного абонемента поточного клієнта.",
            examples=["subscription-501"],
        ),
    ],
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


# Повертає абонементи поточного користувача.
@router.get(
    "/my-subscriptions",
    response_model=list[SubscriptionRead],
    summary="Переглянути власні абонементи",
    description="Повертає історію абонементів поточного клієнта разом із планом і службовими полями.",
    responses=merge_responses(
        {200: response_example("Список абонементів поточного користувача.", [SUBSCRIPTION_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
    ),
)
async def my_subscriptions(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[SubscriptionRead]:
    service = SubscriptionService(db)
    subscriptions = await service.list_for_user(current_user.id)
    return [SubscriptionRead.model_validate(item) for item in subscriptions]
