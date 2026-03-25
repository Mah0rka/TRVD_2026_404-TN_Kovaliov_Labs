# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreateRequest, PaymentRead
from app.services.payment_service import PaymentService

router = APIRouter()


# Працює з checkout-сценарієм платежів.
@router.post("/checkout", response_model=PaymentRead)
async def checkout(
    payload: PaymentCreateRequest,
    current_user: User = Depends(require_roles(UserRole.CLIENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> PaymentRead:
    service = PaymentService(db)
    payment = await service.checkout(current_user.id, payload.amount, payload.method)
    return PaymentRead.model_validate(payment)


# Повертає історію платежів поточного користувача.
@router.get("/my-payments", response_model=list[PaymentRead])
async def my_payments(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[PaymentRead]:
    service = PaymentService(db)
    payments = await service.list_for_user(current_user.id)
    return [PaymentRead.model_validate(item) for item in payments]


# Повертає реєстр платежів з фільтрами для адміністрації.
@router.get("", response_model=list[PaymentRead])
async def all_payments(
    user_id: str | None = Query(default=None, alias="userId"),
    status_filter: str | None = Query(default=None, alias="status"),
    method: str | None = Query(default=None, alias="method"),
    start_date: datetime | None = Query(default=None, alias="startDate"),
    end_date: datetime | None = Query(default=None, alias="endDate"),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[PaymentRead]:
    service = PaymentService(db)
    payments = await service.list_all(user_id, status_filter, method, start_date, end_date)
    return [PaymentRead.model_validate(item) for item in payments]
