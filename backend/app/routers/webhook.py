from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.config import settings
from app.services.reviewer import run_review
from app.services.github import GitHubClient
from app.services.findings import compute_overall_severity, compute_finding_counts
import hmac
import hashlib
import json

router = APIRouter(prefix="/webhook", tags=["webhook"])


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify the GitHub webhook HMAC-SHA256 signature."""
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_pr_review(
    owner: str,
    repo: str,
    pr_number: int,
    pr_title: str,
    installation_id: int,
) -> None:
    """Fetch PR diff, run review, and post results as GitHub PR review comments."""
    client = GitHubClient(installation_id=installation_id)
    try:
        diff = await client.get_pr_diff(owner, repo, pr_number)
        findings, model = await run_review(diff, pr_title)
        overall = compute_overall_severity(findings)
        counts = compute_finding_counts(findings)

        severity_emoji = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵",
            "info": "⚪",
        }

        overall_val = overall.value if overall else "info"
        overall_label = (overall.value if overall else "PASS").upper()

        top_findings = sorted(
            [
                f
                for f in findings
                if (f.severity if isinstance(f.severity, str) else f.severity.value)
                in ("critical", "high")
            ],
            key=lambda x: ["critical", "high", "medium", "low", "info"].index(
                x.severity if isinstance(x.severity, str) else x.severity.value
            ),
        )[:3]

        body_lines = [
            f"## {severity_emoji.get(overall_val, '⚪')} Sentinel AI Review: {overall_label}",
            "",
            (
                f"**{counts.get('critical', 0)} critical** · "
                f"**{counts.get('high', 0)} high** · "
                f"**{counts.get('medium', 0)} medium** · "
                f"**{counts.get('low', 0)} low**"
            ),
            "",
        ]

        if top_findings:
            body_lines.append("### Top Findings")
            for f in top_findings:
                sev_val = f.severity if isinstance(f.severity, str) else f.severity.value
                emoji = severity_emoji.get(sev_val, "⚪")
                body_lines.append(f"- {emoji} **{f.title}**")
                if f.file_path:
                    line_ref = f" L{f.line_start}" if f.line_start else ""
                    body_lines.append(f"  - `{f.file_path}`{line_ref}")
                body_lines.append(f"  - {f.explanation[:200]}")

        body_lines.extend(
            [
                "",
                "*Powered by [Sentinel Review](https://sentinel-review.vercel.app)*",
            ]
        )

        # Build inline comments (max 20 per GitHub's review API limit)
        inline_comments = []
        for f in findings:
            if f.file_path and f.line_start:
                sev_val = f.severity if isinstance(f.severity, str) else f.severity.value
                comment_body = f"**{sev_val.upper()}: {f.title}**\n\n{f.explanation}"
                if f.suggested_fix:
                    comment_body += (
                        f"\n\n**Suggested fix:**\n```\n{f.suggested_fix}\n```"
                    )
                inline_comments.append(
                    {
                        "path": f.file_path,
                        "line": f.line_start,
                        "body": comment_body,
                    }
                )

        await client.post_pr_review(
            owner,
            repo,
            pr_number,
            body="\n".join(body_lines),
            comments=inline_comments[:20],
        )

    except Exception as e:
        print(f"Error reviewing PR {owner}/{repo}#{pr_number}: {e}")


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive and validate GitHub App webhook events.

    Handles pull_request opened/synchronize events by triggering background review.
    """
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(payload_bytes, signature):
        raise HTTPException(401, "Invalid webhook signature")

    event = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(payload_bytes)

    if event == "pull_request" and payload.get("action") in ("opened", "synchronize"):
        pr = payload["pull_request"]
        installation = payload.get("installation", {})

        background_tasks.add_task(
            handle_pr_review,
            owner=payload["repository"]["owner"]["login"],
            repo=payload["repository"]["name"],
            pr_number=pr["number"],
            pr_title=pr["title"],
            installation_id=installation.get("id"),
        )

    return {"status": "ok"}
