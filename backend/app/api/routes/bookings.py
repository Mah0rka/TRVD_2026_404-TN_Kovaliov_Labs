# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_REQUIRED_RESPONSE,
    BOOKING_EXAMPLE,
    PAYMENT_EXAMPLE,
    PERMISSION_DENIED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
    bad_request_response,
    merge_responses,
    not_found_response,
    response_example,
)
from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.booking import BookingRead
from app.schemas.payment import PaymentRead
from app.services.booking_service import BookingService

router = APIRouter()


# Створює бронювання заняття для клієнта.
@router.post(
    "/{class_id}",
    response_model=BookingRead,
    summary="Записатися на заняття",
    description=(
        "Створює або повторно активує бронювання на безкоштовне заняття для поточного клієнта. "
        "Для платних персональних занять спочатку треба пройти checkout доплати."
    ),
    responses=merge_responses(
        {200: response_example("Бронювання успішно створено.", BOOKING_EXAMPLE)},
        bad_request_response(
            "Бізнес-правила не дозволяють створити бронювання.",
            "Для запису на заняття потрібен активний абонемент",
        ),
        not_found_response("Заняття з указаним ідентифікатором не знайдено.", "Заняття не знайдено"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def create_booking(
    class_id: str = Path(description="Ідентифікатор заняття, на яке записується клієнт.", examples=["class-2026-04-01-0800"]),
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.create_booking(current_user.id, class_id)
    return BookingRead.model_validate(booking)


# Запускає оплату додаткового платного бронювання.
@router.post(
    "/{class_id}/checkout",
    response_model=PaymentRead,
    summary="Створити checkout для платного заняття",
    description=(
        "Створює або повертає pending-платіж за платне персональне заняття. "
        "Після цього клієнт має окремо підтвердити платіж через endpoint confirm."
    ),
    responses=merge_responses(
        {200: response_example("Checkout для доплати створено або знайдено.", PAYMENT_EXAMPLE)},
        bad_request_response(
            "Неможливо створити checkout через стан заняття, абонемента або існуючого запису.",
            "Для цього заняття окрема доплата не потрібна",
        ),
        not_found_response("Заняття з указаним ідентифікатором не знайдено.", "Заняття не знайдено"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def create_paid_booking_checkout(
    class_id: str = Path(
        description="Ідентифікатор платного заняття, для якого треба створити доплату.",
        examples=["class-2026-04-02-1800"],
    ),
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> PaymentRead:
    service = BookingService(db)
    payment = await service.create_paid_booking_checkout(current_user.id, class_id)
    return PaymentRead.model_validate(payment)


# Підтверджує платіж і завершує створення платного бронювання.
@router.post(
    "/payments/{payment_id}/confirm",
    response_model=BookingRead,
    summary="Підтвердити оплату й завершити бронювання",
    description=(
        "Переводить pending-доплату у статус success і створює підтверджене бронювання "
        "для відповідного платного заняття."
    ),
    responses=merge_responses(
        {200: response_example("Оплату підтверджено, бронювання активне.", BOOKING_EXAMPLE)},
        bad_request_response(
            "Платіж уже підтверджений, невалідний для confirm або заняття більше не доступне.",
            "Цю доплату вже не можна підтвердити",
        ),
        not_found_response("Доплату або заняття не знайдено.", "Доплату не знайдено"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def confirm_paid_booking(
    payment_id: str = Path(
        description="Ідентифікатор платежу, отриманий із checkout для платного заняття.",
        examples=["payment-9001"],
    ),
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.confirm_paid_booking(current_user.id, payment_id)
    return BookingRead.model_validate(booking)


# Скасовує бронювання з урахуванням правил повернення візиту.
@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingRead,
    summary="Скасувати власне бронювання",
    description=(
        "Скасовує бронювання поточного клієнта. Якщо правила дозволяють, система "
        "повертає візит на абонемент і змінює статус бронювання на CANCELLED."
    ),
    responses=merge_responses(
        {200: response_example("Бронювання успішно скасовано.", {**BOOKING_EXAMPLE, "status": "CANCELLED"})},
        bad_request_response(
            "Скасування недоступне через часове вікно, статус бронювання або власника запису.",
            "Безкоштовне заняття можна скасувати не пізніше ніж за 1 годину до початку",
        ),
        not_found_response("Бронювання з указаним ідентифікатором не знайдено.", "Booking not found"),
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def cancel_booking(
    booking_id: str = Path(
        description="Ідентифікатор бронювання, яке потрібно скасувати.",
        examples=["booking-3021"],
    ),
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.cancel_booking(current_user.id, booking_id)
    return BookingRead.model_validate(booking)


# Повертає бронювання поточного користувача.
@router.get(
    "/my-bookings",
    response_model=list[BookingRead],
    summary="Переглянути свої бронювання",
    description="Повертає список усіх бронювань поточного клієнта разом з короткими даними заняття.",
    responses=merge_responses(
        {200: response_example("Список бронювань поточного користувача.", [BOOKING_EXAMPLE])},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
    ),
)
async def my_bookings(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[BookingRead]:
    service = BookingService(db)
    bookings = await service.list_for_user(current_user.id)
    return [BookingRead.model_validate(item) for item in bookings]
