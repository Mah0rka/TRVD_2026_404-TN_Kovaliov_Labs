from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_roles
from app.models.user import User, UserRole
from app.schemas.report import RevenueReport, TrainerPopularityReport
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/revenue", response_model=RevenueReport)
async def revenue(
    start_date: datetime | None = Query(default=None, alias="startDate"),
    end_date: datetime | None = Query(default=None, alias="endDate"),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> RevenueReport:
    service = ReportService(db)
    resolved_end = end_date or datetime.utcnow()
    resolved_start = start_date or (resolved_end - timedelta(days=30))
    return await service.revenue_report(resolved_start, resolved_end)


@router.get("/trainers/popularity", response_model=list[TrainerPopularityReport])
async def trainer_popularity(
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainerPopularityReport]:
    service = ReportService(db)
    return await service.trainer_popularity()
