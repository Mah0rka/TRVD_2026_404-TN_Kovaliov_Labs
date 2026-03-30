# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    AUTH_REQUIRED_RESPONSE,
    PERMISSION_DENIED_RESPONSE,
    REVENUE_REPORT_EXAMPLE,
    TRAINER_POPULARITY_EXAMPLE,
    VALIDATION_ERROR_RESPONSE,
    merge_responses,
    response_example,
)
from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.report import RevenueReport, TrainerPopularityReport
from app.services.report_service import ReportService

router = APIRouter()


# Повертає агрегований звіт по доходах за вибраний період.
@router.get(
    "/revenue",
    response_model=RevenueReport,
    summary="Побудувати звіт по доходах",
    description=(
        "Повертає агрегований дохід за вказаний період. Якщо дати не передані, API бере "
        "останні 30 днів до поточного моменту."
    ),
    responses=merge_responses(
        {200: response_example("Агрегований revenue report за вибраний період.", REVENUE_REPORT_EXAMPLE)},
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
        VALIDATION_ERROR_RESPONSE,
    ),
)
async def revenue(
    start_date: datetime | None = Query(
        default=None,
        alias="startDate",
        description="Початок звітного періоду в ISO 8601.",
        examples=["2026-03-01T00:00:00Z"],
    ),
    end_date: datetime | None = Query(
        default=None,
        alias="endDate",
        description="Кінець звітного періоду в ISO 8601.",
        examples=["2026-03-31T23:59:59Z"],
    ),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> RevenueReport:
    service = ReportService(db)
    resolved_end = end_date or datetime.now(UTC)
    resolved_start = start_date or (resolved_end - timedelta(days=30))
    return await service.revenue_report(resolved_start, resolved_end)


# Повертає статистику популярності тренерів.
@router.get(
    "/trainers/popularity",
    response_model=list[TrainerPopularityReport],
    summary="Оцінити популярність тренерів",
    description=(
        "Повертає рейтинг тренерів за кількістю відвідувачів і середнім заповненням їхніх занять."
    ),
    responses=merge_responses(
        {
            200: response_example(
                "Список тренерів з показниками популярності.",
                [TRAINER_POPULARITY_EXAMPLE],
            )
        },
        AUTH_REQUIRED_RESPONSE,
        PERMISSION_DENIED_RESPONSE,
    ),
)
async def trainer_popularity(
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainerPopularityReport]:
    service = ReportService(db)
    return await service.trainer_popularity()
