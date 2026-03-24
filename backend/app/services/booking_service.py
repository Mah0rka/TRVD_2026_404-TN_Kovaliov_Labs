from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.subscription import SubscriptionStatus
from app.models.workout_class import WorkoutClass
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.models.payment import Payment


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.booking_repository = BookingRepository(session)
        self.subscription_repository = SubscriptionRepository(session)
        self.payment_repository = PaymentRepository(session)

    async def create_booking(self, user_id: str, class_id: str) -> Booking:
        try:
            workout_class = await self.session.get(WorkoutClass, class_id)
            if not workout_class:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заняття не знайдено")

            if workout_class.is_paid_extra:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для платного заняття спочатку створіть і підтвердьте доплату",
                )

            current_bookings_count = await self.booking_repository.count_confirmed_for_class(class_id)
            if current_bookings_count >= workout_class.capacity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="На це заняття вже немає вільних місць")

            if not workout_class.is_paid_extra:
                same_day_bookings = await self._list_non_paid_bookings_for_day(user_id, workout_class.start_time)
                if any(booking.class_id != class_id for booking in same_day_bookings):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="На один день можна записатися лише на одне безкоштовне заняття",
                    )

            existing_booking = await self.booking_repository.get_by_user_and_class(user_id, class_id)
            if existing_booking:
                if existing_booking.status == BookingStatus.CONFIRMED:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ви вже записані на це заняття")

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
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Можна скасувати лише власний запис")

            class_time = booking.workout_class.start_time
            if class_time.tzinfo is None:
                class_time = class_time.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            hours_difference = (class_time - now).total_seconds() / 3600
            cancellation_window_hours = 1 if not booking.workout_class.is_paid_extra else 2
            if hours_difference < cancellation_window_hours:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Безкоштовне заняття можна скасувати не пізніше ніж за 1 годину до початку"
                        if not booking.workout_class.is_paid_extra
                        else "Платне заняття можна скасувати не пізніше ніж за 2 години до початку"
                    ),
                )

            if booking.status == BookingStatus.CANCELLED:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Цей запис уже скасовано")

            booking.status = BookingStatus.CANCELLED
            active_subscription = await self.subscription_repository.get_active_by_user(user_id)
            if (
                active_subscription
                and active_subscription.total_visits is not None
                and not booking.workout_class.is_paid_extra
            ):
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

    async def create_paid_booking_checkout(self, user_id: str, class_id: str) -> Payment:
        workout_class = await self.session.get(WorkoutClass, class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заняття не знайдено")
        if not workout_class.is_paid_extra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для цього заняття окрема доплата не потрібна",
            )

        current_bookings_count = await self.booking_repository.count_confirmed_for_class(class_id)
        if current_bookings_count >= workout_class.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="На це заняття вже немає вільних місць")

        existing_booking = await self.booking_repository.get_by_user_and_class(user_id, class_id)
        if existing_booking and existing_booking.status == BookingStatus.CONFIRMED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ви вже записані на це заняття")

        active_subscription = await self.subscription_repository.get_active_by_user(user_id)
        self._validate_subscription_for_booking(active_subscription, paid_message=True)

        pending_payment = await self.payment_repository.get_pending_booking_payment(user_id, class_id)
        if pending_payment:
            return pending_payment

        payment = Payment(
            user_id=user_id,
            amount=workout_class.extra_price or 0,
            currency="UAH",
            status="PENDING",
            method="CARD",
            purpose="BOOKING_EXTRA",
            description=f"Доплата за заняття: {workout_class.title}",
            booking_class_id=class_id,
        )
        self.session.add(payment)
        await self.session.commit()
        created_payment = await self.payment_repository.get_by_id(payment.id)
        assert created_payment is not None
        return created_payment

    async def confirm_paid_booking(self, user_id: str, payment_id: str) -> Booking:
        payment = await self.payment_repository.get_by_id(payment_id)
        if not payment or payment.user_id != user_id or payment.purpose != "BOOKING_EXTRA" or not payment.booking_class_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Доплату не знайдено")
        if payment.status == "SUCCESS":
            existing_booking = await self.booking_repository.get_by_user_and_class(user_id, payment.booking_class_id)
            if existing_booking and existing_booking.status == BookingStatus.CONFIRMED:
                return existing_booking
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Оплата вже підтверджена")
        if payment.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Цю доплату вже не можна підтвердити")

        workout_class = await self.session.get(WorkoutClass, payment.booking_class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заняття не знайдено")
        if not workout_class.is_paid_extra:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Це заняття не потребує окремої доплати")

        current_bookings_count = await self.booking_repository.count_confirmed_for_class(workout_class.id)
        if current_bookings_count >= workout_class.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="На це заняття вже немає вільних місць")

        existing_booking = await self.booking_repository.get_by_user_and_class(user_id, workout_class.id)
        if existing_booking and existing_booking.status == BookingStatus.CONFIRMED:
            payment.status = "SUCCESS"
            await self.session.commit()
            return existing_booking

        active_subscription = await self.subscription_repository.get_active_by_user(user_id)
        self._validate_subscription_for_booking(active_subscription, paid_message=True)

        if existing_booking and existing_booking.status == BookingStatus.CANCELLED:
            existing_booking.status = BookingStatus.CONFIRMED
            booking_id = existing_booking.id
        else:
            booking = Booking(
                user_id=user_id,
                class_id=workout_class.id,
                status=BookingStatus.CONFIRMED,
            )
            self.session.add(booking)
            await self.session.flush()
            booking_id = booking.id

        payment.status = "SUCCESS"
        payment.description = f"Оплачено персональне заняття: {workout_class.title}"
        await self.session.commit()

        created_booking = await self.booking_repository.get_by_id(booking_id)
        assert created_booking is not None
        return created_booking

    async def _consume_visit_if_needed(self, active_subscription):
        self._validate_subscription_for_booking(active_subscription)

        if active_subscription.total_visits is None:
            return

        remaining_visits = active_subscription.remaining_visits or 0
        active_subscription.remaining_visits = remaining_visits - 1

    async def _list_non_paid_bookings_for_day(self, user_id: str, class_start_time: datetime) -> list[Booking]:
        club_tz = ZoneInfo("Europe/Kiev")
        localized_start = class_start_time.astimezone(club_tz)
        day_start_local = datetime.combine(localized_start.date(), time.min, tzinfo=club_tz)
        day_end_local = day_start_local + timedelta(days=1)
        day_start_utc = day_start_local.astimezone(UTC)
        day_end_utc = day_end_local.astimezone(UTC)
        bookings = await self.booking_repository.list_confirmed_for_user_between(user_id, day_start_utc, day_end_utc)
        return [booking for booking in bookings if not booking.workout_class.is_paid_extra]

    @staticmethod
    def _validate_subscription_for_booking(active_subscription, *, paid_message: bool = False) -> None:
        if not active_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Для платного персонального заняття потрібен активний абонемент"
                    if paid_message
                    else "Для запису на заняття потрібен активний абонемент"
                ),
            )

        if active_subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Абонемент неактивний")

        if active_subscription.total_visits is not None:
            remaining_visits = active_subscription.remaining_visits or 0
            if remaining_visits <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У вашому абонементі не залишилося відвідувань",
                )
