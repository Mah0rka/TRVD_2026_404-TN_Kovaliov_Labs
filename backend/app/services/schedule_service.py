from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.models.user import User
from app.models.workout_class import WorkoutClass
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ScheduleRepository(session)
        self.booking_repository = BookingRepository(session)

    async def create_schedule(self, payload: ScheduleCreate, current_user: User) -> WorkoutClass:
        if payload.end_time <= payload.start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

        workout_class = WorkoutClass(
            title=payload.title.strip(),
            type=payload.type,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
            trainer_id=payload.trainer_id or current_user.id,
        )
        created = await self.repository.create(workout_class)
        refreshed = await self.repository.get_by_id(created.id)
        assert refreshed is not None
        return refreshed

    async def list_schedules(self) -> list[WorkoutClass]:
        return await self.repository.list_all()

    async def list_my_classes(self, trainer_id: str) -> list[WorkoutClass]:
        return await self.repository.list_by_trainer(trainer_id)

    async def update_schedule(self, class_id: str, payload: ScheduleUpdate) -> WorkoutClass:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        for field_name, value in update_data.items():
            setattr(workout_class, field_name, value)

        if workout_class.end_time <= workout_class.start_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

        await self.repository.commit()
        refreshed = await self.repository.get_by_id(class_id)
        assert refreshed is not None
        return refreshed

    async def delete_schedule(self, class_id: str) -> None:
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        await self.repository.delete(workout_class)

    async def list_attendees(self, class_id: str, current_user: User):
        workout_class = await self.repository.get_by_id(class_id)
        if not workout_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        allowed_roles = {UserRole.ADMIN, UserRole.OWNER}
        if current_user.role not in allowed_roles and workout_class.trainer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        return await self.booking_repository.list_attendees_for_class(class_id)
