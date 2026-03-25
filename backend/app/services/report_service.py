# Сервіс інкапсулює бізнес-правила та координує роботу репозиторіїв.

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment
from app.models.user import User
from app.models.workout_class import WorkoutClass
from app.schemas.report import RevenueReport, TrainerPopularityReport


class ReportService:
    # Ініціалізує внутрішній стан обʼєкта.
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Обслуговує сценарій revenue report.
    async def revenue_report(self, start_date: datetime, end_date: datetime) -> RevenueReport:
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0), func.count(Payment.id)).where(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
                Payment.status == "SUCCESS",
            )
        )
        total_revenue, transactions_count = result.one()
        return RevenueReport(
            period={"startDate": start_date, "endDate": end_date},
            total_revenue=float(total_revenue),
            transactions_count=int(transactions_count),
            currency="UAH",
        )

    # Повертає статистику популярності тренерів.
    async def trainer_popularity(self) -> list[TrainerPopularityReport]:
        result = await self.session.execute(
            select(
                User.id,
                User.first_name,
                User.last_name,
                func.count(func.distinct(WorkoutClass.id)),
                func.count(Booking.id),
            )
            .join(WorkoutClass, WorkoutClass.trainer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.class_id == WorkoutClass.id) & (Booking.status == BookingStatus.CONFIRMED),
            )
            .group_by(User.id, User.first_name, User.last_name)
            .order_by(func.count(Booking.id).desc())
        )

        reports: list[TrainerPopularityReport] = []
        for trainer_id, first_name, last_name, classes_taught, total_attendees in result.all():
            classes_taught = int(classes_taught)
            total_attendees = int(total_attendees)
            reports.append(
                TrainerPopularityReport(
                    trainer_id=trainer_id,
                    name=f"{first_name} {last_name}",
                    total_attendees=total_attendees,
                    classes_taught=classes_taught,
                    average_attendees_per_class=(
                        total_attendees / classes_taught if classes_taught else 0.0
                    ),
                )
            )
        return reports
