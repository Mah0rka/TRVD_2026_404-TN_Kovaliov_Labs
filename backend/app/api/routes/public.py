from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.public import ClubStats
from app.services.public_service import PublicService

router = APIRouter()


@router.get("/club-stats", response_model=ClubStats)
async def club_stats(db: AsyncSession = Depends(get_db_session)) -> ClubStats:
    service = PublicService(db)
    return await service.club_stats()
