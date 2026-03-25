# Коротко: маршрут обробляє HTTP-запити для модуля публічних даних.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.membership_plan import MembershipPlanRead
from app.schemas.public import ClubStats
from app.services.public_service import PublicService

router = APIRouter()


@router.get("/club-stats", response_model=ClubStats)
async def club_stats(db: AsyncSession = Depends(get_db_session)) -> ClubStats:
    service = PublicService(db)
    return await service.club_stats()


@router.get("/membership-plans", response_model=list[MembershipPlanRead])
async def public_membership_plans(db: AsyncSession = Depends(get_db_session)) -> list[MembershipPlanRead]:
    service = PublicService(db)
    plans = await service.membership_plans()
    return [MembershipPlanRead.model_validate(plan) for plan in plans]
