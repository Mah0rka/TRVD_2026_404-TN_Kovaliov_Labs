# Коротко: репозиторій інкапсулює доступ до даних для модуля бронювань.

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.workout_class import WorkoutClass


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: str) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.workout_class).selectinload(WorkoutClass.trainer),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_class(self, user_id: str, class_id: str) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(Booking.user_id == user_id, Booking.class_id == class_id)
        )
        return result.scalar_one_or_none()

    async def count_confirmed_for_class(self, class_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Booking.id)).where(
                Booking.class_id == class_id,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        return int(result.scalar_one())

    async def list_by_user(self, user_id: str) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .options(
                selectinload(Booking.workout_class).selectinload(WorkoutClass.trainer),
            )
            .order_by(Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_attendees_for_class(self, class_id: str) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.class_id == class_id, Booking.status == BookingStatus.CONFIRMED)
            .options(selectinload(Booking.user), selectinload(Booking.workout_class))
            .order_by(Booking.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_confirmed_for_user_between(
        self,
        user_id: str,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .join(Booking.workout_class)
            .where(
                Booking.user_id == user_id,
                Booking.status == BookingStatus.CONFIRMED,
                WorkoutClass.start_time >= start_datetime,
                WorkoutClass.start_time < end_datetime,
            )
            .options(selectinload(Booking.workout_class))
            .order_by(WorkoutClass.start_time.asc())
        )
        return list(result.scalars().all())
