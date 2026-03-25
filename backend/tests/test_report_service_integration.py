# Тести перевіряють ключові сценарії цього модуля.

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.models.workout_class import WorkoutClass, WorkoutType
from app.services.report_service import ReportService


# Перевіряє, що revenue report aggregates successful payments працює коректно.
@pytest.mark.asyncio
async def test_revenue_report_aggregates_successful_payments(db_session):
    client = User(
        email="report-client@test.local",
        password_hash="hash",
        first_name="Report",
        last_name="Client",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add(client)
    await db_session.flush()

    db_session.add_all(
        [
            Payment(
                user_id=client.id,
                amount=Decimal("100.00"),
                currency="UAH",
                status="SUCCESS",
                method="CARD",
            ),
            Payment(
                user_id=client.id,
                amount=Decimal("50.00"),
                currency="UAH",
                status="FAILED",
                method="CARD",
            ),
            Payment(
                user_id=client.id,
                amount=Decimal("40.00"),
                currency="UAH",
                status="SUCCESS",
                method="CASH",
            ),
        ]
    )
    await db_session.commit()

    service = ReportService(db_session)
    report = await service.revenue_report(
        datetime.now(UTC) - timedelta(days=1),
        datetime.now(UTC) + timedelta(days=1),
    )

    assert report.total_revenue == 140.0
    assert report.transactions_count == 2
    assert report.currency == "UAH"


# Перевіряє, що trainer popularity counts confirmed bookings працює коректно.
@pytest.mark.asyncio
async def test_trainer_popularity_counts_confirmed_bookings(db_session):
    trainer = User(
        email="trainer-report@test.local",
        password_hash="hash",
        first_name="Trainer",
        last_name="Report",
        role=UserRole.TRAINER,
        is_verified=True,
    )
    client = User(
        email="client-report@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Report",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    second_client = User(
        email="client-report-2@test.local",
        password_hash="hash",
        first_name="Client",
        last_name="Two",
        role=UserRole.CLIENT,
        is_verified=True,
    )
    db_session.add_all([trainer, client, second_client])
    await db_session.flush()

    start_time = datetime.now(UTC) + timedelta(days=1)
    workout_class = WorkoutClass(
        title="Report Class",
        trainer_id=trainer.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        capacity=12,
        type=WorkoutType.GROUP,
    )
    db_session.add(workout_class)
    await db_session.flush()

    db_session.add_all(
        [
            Booking(
                user_id=client.id,
                class_id=workout_class.id,
                status=BookingStatus.CONFIRMED,
            ),
            Booking(
                user_id=second_client.id,
                class_id=workout_class.id,
                status=BookingStatus.CANCELLED,
            ),
        ]
    )
    await db_session.commit()

    service = ReportService(db_session)
    reports = await service.trainer_popularity()

    assert len(reports) == 1
    assert reports[0].name == "Trainer Report"
    assert reports[0].classes_taught == 1
    assert reports[0].total_attendees == 1
