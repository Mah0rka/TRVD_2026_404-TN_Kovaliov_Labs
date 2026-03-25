# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.booking import BookingRead
from app.schemas.payment import PaymentRead
from app.services.booking_service import BookingService

router = APIRouter()


# Створює бронювання заняття для клієнта.
@router.post("/{class_id}", response_model=BookingRead)
async def create_booking(
    class_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.create_booking(current_user.id, class_id)
    return BookingRead.model_validate(booking)


# Запускає оплату додаткового платного бронювання.
@router.post("/{class_id}/checkout", response_model=PaymentRead)
async def create_paid_booking_checkout(
    class_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> PaymentRead:
    service = BookingService(db)
    payment = await service.create_paid_booking_checkout(current_user.id, class_id)
    return PaymentRead.model_validate(payment)


# Підтверджує платіж і завершує створення платного бронювання.
@router.post("/payments/{payment_id}/confirm", response_model=BookingRead)
async def confirm_paid_booking(
    payment_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.confirm_paid_booking(current_user.id, payment_id)
    return BookingRead.model_validate(booking)


# Скасовує бронювання з урахуванням правил повернення візиту.
@router.patch("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.cancel_booking(current_user.id, booking_id)
    return BookingRead.model_validate(booking)


# Повертає бронювання поточного користувача.
@router.get("/my-bookings", response_model=list[BookingRead])
async def my_bookings(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[BookingRead]:
    service = BookingService(db)
    bookings = await service.list_for_user(current_user.id)
    return [BookingRead.model_validate(item) for item in bookings]
