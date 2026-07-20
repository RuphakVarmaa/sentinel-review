from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.review import ReviewRequest, ReviewResponse, FindingCounts
from app.services.reviewer import run_review, stream_review
from app.services.rate_limiter import check_rate_limit
from app.services.github import GitHubClient
from app.services.diff_parser import parse_diff
from app.services.findings import compute_overall_severity, compute_finding_counts
import uuid
import re
import time

router = APIRouter(prefix="/v1", tags=["review"])


@router.post("/review", response_model=ReviewResponse)
async def create_review(req: ReviewRequest, request: Request):
    """Submit a diff for synchronous AI code review.

    Accepts either a raw diff string or a public GitHub PR URL.
    Returns aggregated findings from 5 parallel analysis agents.
    """
    await check_rate_limit(request)

    diff = req.diff or ""

    # If pr_url provided and no diff, fetch from GitHub
    if req.pr_url and not diff.strip():
        client = GitHubClient()
        match = re.match(
            r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', req.pr_url
        )
        if not match:
            raise HTTPException(400, "Invalid GitHub PR URL")
        try:
            diff, _, _ = await client.get_public_pr_diff(req.pr_url)
        except Exception:
            raise HTTPException(
                400,
                "Could not fetch PR diff. Ensure the PR is from a public repository.",
            )

    if not diff or not diff.strip():
        raise HTTPException(400, "No diff provided")

    share_id = uuid.uuid4().hex[:8]

    start = time.time()
    findings, model = await run_review(diff, req.context)
    latency_ms = int((time.time() - start) * 1000)

    overall = compute_overall_severity(findings)
    raw_counts = compute_finding_counts(findings)
    counts = FindingCounts(**raw_counts)
    review_id = uuid.uuid4()

    return ReviewResponse(
        review_id=review_id,
        overall_severity=overall,
        finding_counts=counts,
        model_used=model,
        latency_ms=latency_ms,
        findings=findings,
        share_id=share_id,
    )


@router.post("/review/stream")
async def stream_review_endpoint(req: ReviewRequest, request: Request):
    """Submit a diff for streaming AI code review via Server-Sent Events.

    Streams status, finding, summary, and done events as analysis progresses.
    """
    await check_rate_limit(request)

    diff = req.diff or ""

    if req.pr_url and not diff.strip():
        client = GitHubClient()
        match = re.match(
            r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', req.pr_url
        )
        if not match:
            raise HTTPException(400, "Invalid GitHub PR URL")
        try:
            diff, _, _ = await client.get_public_pr_diff(req.pr_url)
        except Exception:
            raise HTTPException(400, "Could not fetch PR diff")

    if not diff or not diff.strip():
        raise HTTPException(400, "No diff provided")

    return StreamingResponse(
        stream_review(diff, req.context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
