# Сервіс інкапсулює бізнес-правила та координує роботу репозиторіїв.

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.models.user import User
from app.models.workout_class import WorkoutClass
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.schedule import ScheduleCompleteRequest, ScheduleCreate, ScheduleUpdate


class ScheduleService:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ScheduleRepository(session)
        self.booking_repository = BookingRepository(session)

    # Створює schedule.
    async def create_schedule(self, payload: ScheduleCreate, current_user: User) -> WorkoutClass:
        if payload.end_time <= payload.start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Час завершення має бути пізніше за час початку")
        self._validate_pricing(payload.is_paid_extra, payload.extra_price)

        workout_class = WorkoutClass(
            title=payload.title.strip(),
            type=payload.type,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
            trainer_id=payload.trainer_id or current_user.id,
            is_paid_extra=payload.is_paid_extra,
            extra_price=payload.extra_price if payload.is_paid_extra else None,
        )
        created = await self.repository.create(workout_class)
        refreshed = await self.repository.get_by_id(created.id)
        assert refreshed is not None
        return refreshed

    # Повертає список schedules.
    async def list_schedules(self) -> list[WorkoutClass]:
        return await self.repository.list_all()

    # Повертає список my classes.
    async def list_my_classes(self, trainer_id: str) -> list[WorkoutClass]:
        return await self.repository.list_by_trainer(trainer_id)

    # Оновлює schedule.
    async def update_schedule(self, class_id: str, payload: ScheduleUpdate) -> WorkoutClass:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        for field_name, value in update_data.items():
            setattr(workout_class, field_name, value)

        if workout_class.end_time <= workout_class.start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Час завершення має бути пізніше за час початку")

        self._validate_pricing(workout_class.is_paid_extra, workout_class.extra_price)
        if not workout_class.is_paid_extra:
            workout_class.extra_price = None

        await self.repository.commit()
        refreshed = await self.repository.get_by_id(class_id)
        assert refreshed is not None
        return refreshed

    # Видаляє schedule.
    async def delete_schedule(self, class_id: str) -> None:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        await self.repository.delete(workout_class)

    # Підтверджує, що завершене заняття фактично відбулося.
    async def confirm_completion(
        self,
        class_id: str,
        payload: ScheduleCompleteRequest,
        current_user: User,
    ) -> WorkoutClass:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        allowed_roles = {UserRole.ADMIN, UserRole.OWNER}
        if current_user.role not in allowed_roles and workout_class.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

        now = datetime.now(UTC)
        # Нормалізуємо час завершення, щоб коректно порівнювати aware/naive datetime.
        class_end = workout_class.end_time
        if class_end.tzinfo is None:
            class_end = class_end.replace(tzinfo=UTC)
        if class_end > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заняття можна підтвердити лише після завершення",
            )

        # Перше підтвердження фіксує час, повторне дозволяє оновити коментар без створення дубля.
        workout_class.completed_at = workout_class.completed_at or now
        workout_class.completed_by = current_user
        comment = payload.comment.strip() if payload.comment else None
        workout_class.completion_comment = comment or None
        await self.repository.commit()

        refreshed = await self.repository.get_by_id(class_id)
        assert refreshed is not None
        return refreshed

    # Повертає список attendees.
    async def list_attendees(self, class_id: str, current_user: User):
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        allowed_roles = {UserRole.ADMIN, UserRole.OWNER}
        if current_user.role not in allowed_roles and workout_class.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав доступу")

        return await self.booking_repository.list_attendees_for_class(class_id)

    # Перевіряє pricing.
    @staticmethod
    def _validate_pricing(is_paid_extra: bool, extra_price) -> None:
        if is_paid_extra:
            if extra_price is None or extra_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для платного заняття потрібно вказати додаткову вартість",
                )
