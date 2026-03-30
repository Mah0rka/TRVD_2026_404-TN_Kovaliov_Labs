# Маршрути приймають HTTP-запити, валідовують дані та делегують роботу сервісам.

from fastapi import APIRouter
from sqlalchemy import text

from app.api.docs import HEALTH_LIVE_EXAMPLE, HEALTH_READY_EXAMPLE, response_example
from app.core.database import engine
from app.core.redis import get_redis

router = APIRouter(prefix="/health")


# Повертає просту відповідь для перевірки, що сервіс запущений.
@router.get(
    "/live",
    summary="Перевірити, що API запущене",
    description="Liveness probe для контейнера або балансувальника. Не перевіряє базу даних чи Redis.",
    responses={200: response_example("Сервіс доступний і приймає HTTP-запити.", HEALTH_LIVE_EXAMPLE)},
)
async def live() -> dict[str, str]:
    return {"status": "ok"}


# Повертає відповідь для перевірки готовності сервісу до роботи.
@router.get(
    "/ready",
    summary="Перевірити готовність API до роботи",
    description="Readiness probe: перевіряє доступність бази даних та Redis перед обслуговуванням запитів.",
    responses={200: response_example("Інфраструктурні залежності доступні.", HEALTH_READY_EXAMPLE)},
)
async def ready() -> dict[str, str]:
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))

    redis = get_redis()
    await redis.ping()
    return {"status": "ready"}
