# Репозиторій ізолює читання та запис recurring-серій та їх винятків.

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workout_class import WorkoutClass
from app.models.workout_series import WorkoutSeries, WorkoutSeriesExclusion


class WorkoutSeriesRepository:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Повертає серію разом із винятками та occurrences.
    async def get_by_id(self, series_id: str) -> WorkoutSeries | None:
        result = await self.session.execute(
            select(WorkoutSeries)
            .where(WorkoutSeries.id == series_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(WorkoutSeries.exclusions),
                selectinload(WorkoutSeries.occurrences).selectinload(WorkoutClass.bookings),
                selectinload(WorkoutSeries.trainer),
            )
        )
        return result.scalar_one_or_none()

    # Повертає occurrences серії в межах вікна.
    async def list_occurrences(
        self,
        series_id: str,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[WorkoutClass]:
        query = (
            select(WorkoutClass)
            .where(WorkoutClass.series_id == series_id)
            .execution_options(populate_existing=True)
            .options(selectinload(WorkoutClass.bookings), selectinload(WorkoutClass.trainer))
            .order_by(WorkoutClass.start_time.asc())
        )
        if start_datetime is not None:
            query = query.where(WorkoutClass.start_time >= start_datetime)
        if end_datetime is not None:
            query = query.where(WorkoutClass.start_time <= end_datetime)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # Повертає виняток конкретної дати.
    async def get_exclusion(self, series_id: str, occurrence_start: datetime) -> WorkoutSeriesExclusion | None:
        result = await self.session.execute(
            select(WorkoutSeriesExclusion).where(
                WorkoutSeriesExclusion.series_id == series_id,
                WorkoutSeriesExclusion.occurrence_start == occurrence_start,
            )
        )
        return result.scalar_one_or_none()

    # Додає серію до сесії.
    async def create(self, series: WorkoutSeries) -> WorkoutSeries:
        self.session.add(series)
        await self.session.flush()
        return series

    # Додає виняток серії.
    async def add_exclusion(self, exclusion: WorkoutSeriesExclusion) -> WorkoutSeriesExclusion:
        self.session.add(exclusion)
        await self.session.flush()
        return exclusion

    # Видаляє виняток.
    async def delete_exclusion(self, exclusion: WorkoutSeriesExclusion) -> None:
        await self.session.delete(exclusion)

    # Комітить зміни.
    async def commit(self) -> None:
        await self.session.commit()
