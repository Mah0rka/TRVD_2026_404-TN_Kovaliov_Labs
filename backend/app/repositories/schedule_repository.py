# Коротко: репозиторій інкапсулює доступ до даних для модуля розкладу.

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workout_class import WorkoutClass


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, workout_class: WorkoutClass) -> WorkoutClass:
        self.session.add(workout_class)
        await self.session.commit()
        await self.session.refresh(workout_class)
        return workout_class

    async def list_all(self) -> list[WorkoutClass]:
        result = await self.session.execute(
            select(WorkoutClass)
            .options(
                selectinload(WorkoutClass.trainer),
                selectinload(WorkoutClass.bookings),
            )
            .order_by(WorkoutClass.start_time.asc())
        )
        return list(result.scalars().all())

    async def list_by_trainer(self, trainer_id: str) -> list[WorkoutClass]:
        result = await self.session.execute(
            select(WorkoutClass)
            .where(WorkoutClass.trainer_id == trainer_id)
            .options(selectinload(WorkoutClass.trainer), selectinload(WorkoutClass.bookings))
            .order_by(WorkoutClass.start_time.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, class_id: str) -> WorkoutClass | None:
        result = await self.session.execute(
            select(WorkoutClass)
            .where(WorkoutClass.id == class_id)
            .options(selectinload(WorkoutClass.trainer), selectinload(WorkoutClass.bookings))
        )
        return result.scalar_one_or_none()

    async def delete(self, workout_class: WorkoutClass) -> None:
        await self.session.delete(workout_class)
        await self.session.commit()

    async def commit(self) -> None:
        await self.session.commit()
