# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import CLUB_STATS_EXAMPLE, MEMBERSHIP_PLAN_EXAMPLE, response_example
from app.api.deps import get_db_session
from app.schemas.membership_plan import MembershipPlanRead
from app.schemas.public import ClubStats
from app.services.public_service import PublicService

router = APIRouter()


# Повертає публічну статистику клубу для головної сторінки.
@router.get(
    "/club-stats",
    response_model=ClubStats,
    summary="Отримати публічну статистику клубу",
    description="Повертає агреговані метрики для лендингу або публічного дашборду клубу.",
    responses={200: response_example("Публічні ключові показники клубу.", CLUB_STATS_EXAMPLE)},
)
async def club_stats(db: AsyncSession = Depends(get_db_session)) -> ClubStats:
    service = PublicService(db)
    return await service.club_stats()


# Повертає лише активні й публічні плани абонементів.
@router.get(
    "/membership-plans",
    response_model=list[MembershipPlanRead],
    summary="Отримати публічні плани абонементів",
    description="Повертає лише активні та публічні тарифи, доступні клієнтам для покупки.",
    responses={200: response_example("Список публічних абонементів.", [MEMBERSHIP_PLAN_EXAMPLE])},
)
async def public_membership_plans(db: AsyncSession = Depends(get_db_session)) -> list[MembershipPlanRead]:
    service = PublicService(db)
    plans = await service.membership_plans()
    return [MembershipPlanRead.model_validate(plan) for plan in plans]
