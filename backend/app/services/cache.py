import json
from app.config import settings

_redis = None
_redis_available = None


async def _get_redis():
    global _redis, _redis_available
    if _redis_available is False:
        return None
    if _redis is None:
        try:
            import redis.asyncio as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            await r.ping()
            _redis = r
            _redis_available = True
        except Exception:
            _redis_available = False
            return None
    return _redis


async def get_cached(key: str) -> dict | None:
    r = await _get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def set_cached(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    r = await _get_redis()
    if not r:
        return
    try:
        await r.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass


async def increment_counter(key: str, ttl_seconds: int = 86400) -> int:
    r = await _get_redis()
    if not r:
        return 1  # no Redis → always allow (rate limiting disabled)
    try:
        pipe = r.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, ttl_seconds)
        results = await pipe.execute()
        return results[0]
    except Exception:
        return 1


async def get_counter(key: str) -> int:
    r = await _get_redis()
    if not r:
        return 0
    try:
        val = await r.get(key)
        return int(val) if val else 0
    except Exception:
        return 0
