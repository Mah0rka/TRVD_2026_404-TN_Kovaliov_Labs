# Тести перевіряють доступ до recurring-серій і їх винятків.

from datetime import UTC, datetime, timedelta

import pytest

from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.models.workout_series import RecurrenceFrequency, WorkoutSeries, WorkoutSeriesExclusion
from app.repositories.workout_series_repository import WorkoutSeriesRepository


# Перевіряє CRUD і фільтрацію recurring-серій через repository.
@pytest.mark.asyncio
async def test_workout_series_repository_crud_and_filters(db_session):
    trainer = User(
        email="series-repository@example.com",
        password_hash="hash",
        first_name="Series",
        last_name="Repository",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    db_session.add(trainer)
    await db_session.commit()

    repository = WorkoutSeriesRepository(db_session)
    start_time = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    series = WorkoutSeries(
        title="Morning Series",
        description="Repository coverage",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        is_paid_extra=False,
        extra_price=None,
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_weekday="WE",
        count=3,
        until=None,
        rule_text="RRULE:FREQ=WEEKLY;BYDAY=WE;COUNT=3",
    )
    created_series = await repository.create(series)
    await repository.commit()

    first_occurrence = WorkoutClass(
        title="Morning Series",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        series_id=created_series.id,
        source_occurrence_start=start_time,
    )
    second_occurrence = WorkoutClass(
        title="Morning Series",
        trainer_id=trainer.id,
        start_time=start_time + timedelta(days=7),
        end_time=start_time + timedelta(days=7, hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
        series_id=created_series.id,
        source_occurrence_start=start_time + timedelta(days=7),
    )
    db_session.add_all([first_occurrence, second_occurrence])
    exclusion = await repository.add_exclusion(
        WorkoutSeriesExclusion(
            series_id=created_series.id,
            occurrence_start=start_time + timedelta(days=14),
        )
    )
    await repository.commit()

    loaded = await repository.get_by_id(created_series.id)
    filtered = await repository.list_occurrences(
        created_series.id,
        start_datetime=start_time + timedelta(days=6),
        end_datetime=start_time + timedelta(days=8),
    )
    loaded_exclusion = await repository.get_exclusion(created_series.id, exclusion.occurrence_start)

    assert loaded is not None
    assert loaded.trainer.email == trainer.email
    assert len(loaded.occurrences) == 2
    assert len(loaded.exclusions) == 1
    assert [item.id for item in filtered] == [second_occurrence.id]
    assert loaded_exclusion is not None

    await repository.delete_exclusion(loaded_exclusion)
    await repository.commit()

    assert await repository.get_exclusion(created_series.id, exclusion.occurrence_start) is None
