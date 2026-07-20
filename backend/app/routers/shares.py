from fastapi import APIRouter, HTTPException, Body
from app.services.cache import get_cached, set_cached
import uuid

router = APIRouter(prefix="/shares", tags=["shares"])


@router.get("/{share_id}")
async def get_shared_review(share_id: str):
    """Retrieve a previously shared review by its short ID.

    Reviews expire after 7 days. Returns 404 if not found or expired.
    """
    cached = await get_cached(f"share:{share_id}")
    if not cached:
        raise HTTPException(404, "Review not found or expired")
    return cached


@router.post("/")
async def create_share(review_data: dict = Body(...)):
    """Persist a review result under a short shareable ID.

    The share link is valid for 7 days.
    """
    share_id = uuid.uuid4().hex[:8]
    await set_cached(
        f"share:{share_id}",
        review_data,
        ttl_seconds=604800,  # 7 days
    )
    return {
        "share_id": share_id,
        "url": f"https://sentinel-review.vercel.app/review/{share_id}",
    }
