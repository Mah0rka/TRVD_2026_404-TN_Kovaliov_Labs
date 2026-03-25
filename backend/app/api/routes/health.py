# Коротко: маршрут обробляє HTTP-запити для модуля стану сервісу.

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import get_redis

router = APIRouter(prefix="/health")


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))

    redis = get_redis()
    await redis.ping()
    return {"status": "ready"}
