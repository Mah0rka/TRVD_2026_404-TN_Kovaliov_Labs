# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_REQUIRED_RESPONSE,
    PAYMENT_CREATE_EXAMPLE,
    PAYMENT_EXAMPLE,
    PERMISSION_DENIED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
    gone_response,
    merge_responses,
    response_example,
)
from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreateRequest, PaymentRead
from app.services.payment_service import PaymentService

router = APIRouter()


# Працює з checkout-сценарієм платежів.
@router.post(
    "/checkout",
    response_model=PaymentRead,
    summary="Спробувати direct top-up",
    description=(
        "Legacy checkout endpoint для прямих поповнень. У поточній бізнес-логіці він навмисно "
        "заблокований і повертає 410 з підказкою купувати абонемент."
    ),
    responses=merge_responses(
        gone_response(
            "Прямі поповнення вимкнені в поточній версії API.",
            "Direct top-up is disabled. Purchase a subscription instead.",
        ),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def checkout(
    payload: PaymentCreateRequest,
    current_user: User = Depends(require_roles(UserRole.CLIENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> PaymentRead:
    service = PaymentService(db)
    payment = await service.checkout(current_user.id, payload.amount, payload.method)
    return PaymentRead.model_validate(payment)


# Повертає історію платежів поточного користувача.
@router.get(
    "/my-payments",
    response_model=list[PaymentRead],
    summary="Переглянути власні платежі",
    description="Повертає історію транзакцій поточного клієнта з основними деталями платежів.",
    responses=merge_responses(
        {200: response_example("Список платежів поточного користувача.", [PAYMENT_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
    ),
)
async def my_payments(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[PaymentRead]:
    service = PaymentService(db)
    payments = await service.list_for_user(current_user.id)
    return [PaymentRead.model_validate(item) for item in payments]


# Повертає реєстр платежів з фільтрами для адміністрації.
@router.get(
    "",
    response_model=list[PaymentRead],
    summary="Отримати реєстр платежів",
    description=(
        "Адміністративний список транзакцій з фільтрацією за користувачем, статусом, методом "
        "оплати та діапазоном дат."
    ),
    responses=merge_responses(
        {200: response_example("Відфільтрований список платежів.", [PAYMENT_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def all_payments(
    user_id: str | None = Query(
        default=None,
        alias="userId",
        description="Необов'язковий UUID користувача для фільтрації реєстру.",
        examples=["user-7f6c4d4c"],
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Фільтр за статусом транзакції, наприклад SUCCESS або PENDING.",
        examples=["SUCCESS"],
    ),
    method: str | None = Query(
        default=None,
        alias="method",
        description="Фільтр за методом оплати, наприклад CARD або CASH.",
        examples=["CARD"],
    ),
    start_date: datetime | None = Query(
        default=None,
        alias="startDate",
        description="Початок періоду вибірки в ISO 8601.",
        examples=["2026-03-01T00:00:00Z"],
    ),
    end_date: datetime | None = Query(
        default=None,
        alias="endDate",
        description="Кінець періоду вибірки в ISO 8601.",
        examples=["2026-03-31T23:59:59Z"],
    ),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[PaymentRead]:
    service = PaymentService(db)
    payments = await service.list_all(user_id, status_filter, method, start_date, end_date)
    return [PaymentRead.model_validate(item) for item in payments]
