from datetime import UTC, datetime, timedelta

import pytest

from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.services.public_service import PublicService


@pytest.mark.asyncio
async def test_club_stats_returns_real_counts_from_database(db_session):
    trainer = User(
        email="stats-trainer@test.local",
        password_hash="hash",
        first_name="Stats",
        last_name="Trainer",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    first_client = User(
        email="stats-client-1@test.local",
        password_hash="hash",
        first_name="Stats",
        last_name="ClientOne",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    second_client = User(
        email="stats-client-2@test.local",
        password_hash="hash",
        first_name="Stats",
        last_name="ClientTwo",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    admin = User(
        email="stats-admin@test.local",
        password_hash="hash",
        first_name="Stats",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add_all([trainer, first_client, second_client, admin])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    in_range_class = WorkoutClass(
        title="In Range",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=12,
        type=WorkoutType.GROUP,
    )
    out_of_range_class = WorkoutClass(
        title="Out of Range",
        trainer_id=trainer.id,
        start_time=datetime.now(UTC) + timedelta(days=10),
        end_time=datetime.now(UTC) + timedelta(days=10, hours=1),
        capacity=10,
        type=WorkoutType.GROUP,
    )
    db_session.add_all([in_range_class, out_of_range_class])

    db_session.add_all(
        [
            Subscription(
                user_id=first_client.id,
                type=SubscriptionType.MONTHLY,
                start_date=datetime.now(UTC),
                end_date=datetime.now(UTC) + timedelta(days=30),
                status=SubscriptionStatus.ACTIVE,
                total_visits=12,
                remaining_visits=12,
            ),
            Subscription(
                user_id=second_client.id,
                type=SubscriptionType.MONTHLY,
                start_date=datetime.now(UTC),
                end_date=datetime.now(UTC) + timedelta(days=30),
                status=SubscriptionStatus.FROZEN,
                total_visits=12,
                remaining_visits=12,
            ),
        ]
    )
    await db_session.commit()

    service = PublicService(db_session)
    stats = await service.club_stats()

    assert stats.clients_count == 2
    assert stats.trainers_count == 1
    assert stats.classes_next_7_days == 1
    assert stats.active_subscriptions_count == 1
