# Репозиторій ізолює читання та запис даних у базі.

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workout_class import WorkoutClass
from app.models.workout_series import WorkoutSeries


class ScheduleRepository:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Створює потрібні дані.
    async def create(self, workout_class: WorkoutClass) -> WorkoutClass:
        self.session.add(workout_class)
        await self.session.flush()
        return workout_class

    # Повертає список all.
    async def list_all(
        self,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[WorkoutClass]:
        query = self._base_query()
        if start_datetime is not None:
            query = query.where(WorkoutClass.start_time >= start_datetime)
        if end_datetime is not None:
            query = query.where(WorkoutClass.start_time <= end_datetime)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Повертає список by trainer.
    async def list_by_trainer(
        self,
        trainer_id: str,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[WorkoutClass]:
        query = self._base_query().where(WorkoutClass.trainer_id == trainer_id)
        if start_datetime is not None:
            query = query.where(WorkoutClass.start_time >= start_datetime)
        if end_datetime is not None:
            query = query.where(WorkoutClass.start_time <= end_datetime)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Повертає by id.
    async def get_by_id(self, class_id: str) -> WorkoutClass | None:
        result = await self.session.execute(self._base_query().where(WorkoutClass.id == class_id))
        return result.scalar_one_or_none()

    # Видаляє потрібні дані.
    async def delete(self, workout_class: WorkoutClass) -> None:
        await self.session.delete(workout_class)

    # Обслуговує сценарій commit.
    async def commit(self) -> None:
        await self.session.commit()

    # Повертає базовий query із потрібними звʼязками.
    @staticmethod
    def _base_query():
        return (
            select(WorkoutClass)
            .execution_options(populate_existing=True)
            .options(
                selectinload(WorkoutClass.trainer),
                selectinload(WorkoutClass.completed_by),
                selectinload(WorkoutClass.bookings),
                selectinload(WorkoutClass.series).selectinload(WorkoutSeries.exclusions),
            )
            .order_by(WorkoutClass.start_time.asc())
        )
