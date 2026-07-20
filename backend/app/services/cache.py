import redis.asyncio as redis
import json
from app.config import settings

_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_cached(key: str) -> dict | None:
    r = await get_redis()
    val = await r.get(key)
    if val:
        return json.loads(val)
    return None


async def set_cached(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    r = await get_redis()
    await r.setex(key, ttl_seconds, json.dumps(value))


async def increment_counter(key: str, ttl_seconds: int = 86400) -> int:
    r = await get_redis()
    pipe = r.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, ttl_seconds)
    results = await pipe.execute()
    return results[0]


async def get_counter(key: str) -> int:
    r = await get_redis()
    val = await r.get(key)
    return int(val) if val else 0
