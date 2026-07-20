"""Background job module for posting GitHub PR review comments.

The primary implementation lives in webhook.handle_pr_review(), which
runs as a FastAPI BackgroundTask immediately after a webhook event.

This module is reserved for future queue-based processing (e.g., Celery,
ARQ, or a Redis-backed job queue) when reviews need to be decoupled from
the webhook handler's response cycle or retried independently.
"""

from typing import Any


async def post_review_comments(
    owner: str,
    repo: str,
    pr_number: int,
    findings: list[dict[str, Any]],
    installation_id: int,
) -> None:
    """Post inline GitHub PR review comments for the given findings.

    Submits up to 10 findings as inline comments on the pull request.
    For security findings, uses GitHub's suggestion syntax where a fix
    is available.

    Args:
        owner: Repository owner (user or organisation).
        repo: Repository name.
        pr_number: Pull request number.
        findings: List of finding dicts with keys:
            severity, title, explanation, file_path, line_start, suggested_fix.
        installation_id: GitHub App installation ID for auth.
    """
    from app.services.github import GitHubClient

    client = GitHubClient(installation_id=installation_id)

    for finding in findings[:10]:
        if finding.get("file_path") and finding.get("line_start"):
            severity = (finding.get("severity") or "info").upper()
            title = finding.get("title", "Finding")
            explanation = finding.get("explanation", "")
            suggested_fix = finding.get("suggested_fix")

            body = f"**{severity}: {title}**\n\n{explanation}"
            if suggested_fix:
                body += f"\n\n```suggestion\n{suggested_fix}\n```"

            await client.post_issue_comment(
                owner=owner,
                repo=repo,
                issue_number=pr_number,
                body=body,
            )
