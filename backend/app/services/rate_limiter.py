from app.services.cache import increment_counter, get_counter
from app.config import settings
from fastapi import HTTPException, Request
import hashlib


def get_client_id(request: Request) -> str:
    """Get a stable client identifier.

    Uses API key from Authorization header if present,
    otherwise hashes the client IP address.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return f"key:{auth[7:]}"
    ip = request.client.host if request.client else "unknown"
    return f"ip:{hashlib.md5(ip.encode()).hexdigest()}"


async def check_rate_limit(request: Request, api_key: str | None = None) -> None:
    """Check and enforce per-day rate limit.

    Raises HTTP 429 if the client has exceeded their daily review limit.
    """
    client_id = api_key if api_key else get_client_id(request)
    key = f"rate:{client_id}:daily"
    count = await increment_counter(key, ttl_seconds=86400)
    limit = settings.FREE_REVIEWS_PER_DAY
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {limit} reviews reached. Upgrade to Pro for unlimited reviews.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )
