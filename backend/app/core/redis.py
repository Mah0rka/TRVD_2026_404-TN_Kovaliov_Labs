# Модуль зберігає спільну інфраструктурну логіку застосунку.

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


# Повертає клієнт Redis для сесій, кешу та лімітів.
def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client
