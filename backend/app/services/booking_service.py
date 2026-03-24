from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.subscription import SubscriptionStatus
from app.models.workout_class import WorkoutClass
from app.repositories.booking_repository import BookingRepository
from app.repositories.subscription_repository import SubscriptionRepository


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.subscription_repository = SubscriptionRepository(session)

    async def create_booking(self, user_id: str, class_id: str) -> Booking:
        try:
            workout_class = await self.session.get(WorkoutClass, class_id)
            if not workout_class:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout class not found")

            current_bookings_count = await self.booking_repository.count_confirmed_for_class(class_id)
            if current_bookings_count >= workout_class.capacity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workout class is full")

            existing_booking = await self.booking_repository.get_by_user_and_class(user_id, class_id)
            if existing_booking:
                if existing_booking.status == BookingStatus.CONFIRMED:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already booked for this class")

                active_subscription = await self.subscription_repository.get_active_by_user(user_id)
                await self._consume_visit_if_needed(active_subscription)
                existing_booking.status = BookingStatus.CONFIRMED
                booking_id = existing_booking.id
            else:
                active_subscription = await self.subscription_repository.get_active_by_user(user_id)
                await self._consume_visit_if_needed(active_subscription)
                booking = Booking(
                    user_id=user_id,
                    class_id=class_id,
                    status=BookingStatus.CONFIRMED,
                )
                self.session.add(booking)
                await self.session.flush()
                booking_id = booking.id
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        created_booking = await self.booking_repository.get_by_id(booking_id)
        assert created_booking is not None
        return created_booking

    async def cancel_booking(self, user_id: str, booking_id: str) -> Booking:
        try:
            booking = await self.booking_repository.get_by_id(booking_id)
            if not booking:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

            if booking.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can only cancel your own bookings")

            class_time = booking.workout_class.start_time
            if class_time.tzinfo is None:
                class_time = class_time.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            hours_difference = (class_time - now).total_seconds() / 3600
            if hours_difference < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel booking less than 2 hours before the class",
                )

            if booking.status == BookingStatus.CANCELLED:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking already cancelled")

            booking.status = BookingStatus.CANCELLED
            active_subscription = await self.subscription_repository.get_active_by_user(user_id)
            if active_subscription and active_subscription.total_visits is not None:
                active_subscription.remaining_visits = (active_subscription.remaining_visits or 0) + 1
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        refreshed = await self.booking_repository.get_by_id(booking_id)
        assert refreshed is not None
        return refreshed

    async def list_for_user(self, user_id: str) -> list[Booking]:
        return await self.booking_repository.list_by_user(user_id)

    async def _consume_visit_if_needed(self, active_subscription):
        if not active_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active subscription is required for booking",
            )

        if active_subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription is not active")

        if active_subscription.total_visits is None:
            return

        remaining_visits = active_subscription.remaining_visits or 0
        if remaining_visits <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No visits remaining")

        active_subscription.remaining_visits = remaining_visits - 1
