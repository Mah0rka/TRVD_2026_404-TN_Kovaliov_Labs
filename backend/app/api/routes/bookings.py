from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.booking import BookingRead
from app.services.booking_service import BookingService

router = APIRouter()


@router.post("/{class_id}", response_model=BookingRead)
async def create_booking(
    class_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.create_booking(current_user.id, class_id)
    return BookingRead.model_validate(booking)


@router.patch("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> BookingRead:
    service = BookingService(db)
    booking = await service.cancel_booking(current_user.id, booking_id)
    return BookingRead.model_validate(booking)


@router.get("/my-bookings", response_model=list[BookingRead])
async def my_bookings(
    current_user: User = Depends(require_roles(UserRole.CLIENT)),
    db: AsyncSession = Depends(get_db_session),
) -> list[BookingRead]:
    service = BookingService(db)
    bookings = await service.list_for_user(current_user.id)
    return [BookingRead.model_validate(item) for item in bookings]
