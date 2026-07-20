import httpx
import jwt
import time
import asyncio
import re
from app.config import settings
from typing import Optional


def generate_jwt() -> str:
    """Generate a GitHub App JWT valid for 10 minutes."""
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": settings.GITHUB_APP_ID,
    }
    return jwt.encode(
        payload,
        settings.GITHUB_APP_PRIVATE_KEY,
        algorithm="RS256",
    )


async def get_installation_token(installation_id: int) -> str:
    """Exchange GitHub App JWT for an installation access token."""
    app_jwt = generate_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    return data["token"]


async def get_pr_diff(
    owner: str, repo: str, pr_number: int, installation_id: int
) -> str:
    """Fetch raw unified diff for a pull request using installation auth."""
    token = await get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3.diff",
            },
            timeout=30,
        )
        resp.raise_for_status()
    return resp.text


async def get_public_pr_diff(pr_url: str) -> tuple[str, str, str]:
    """Fetch diff for a public repo PR without auth.

    Parses github.com/{owner}/{repo}/pull/{number} from URL.
    Returns (diff_text, pr_title, pr_description).
    """
    match = re.match(
        r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url
    )
    if not match:
        raise ValueError(f"Cannot parse GitHub PR URL: {pr_url}")

    owner, repo, pr_number = match.groups()

    async with httpx.AsyncClient() as client:
        # Fetch PR metadata (title + body)
        meta_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=30,
        )
        meta_resp.raise_for_status()
        meta = meta_resp.json()

        # Fetch raw diff
        diff_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
            timeout=30,
        )
        diff_resp.raise_for_status()

    return diff_resp.text, meta.get("title", ""), meta.get("body", "") or ""


async def post_pr_review(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    comments: list[dict],
    installation_id: int,
) -> None:
    """Post a COMMENT-type PR review with optional inline comments."""
    token = await get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "body": body,
                "event": "COMMENT",
                "comments": comments,
            },
            timeout=30,
        )
        resp.raise_for_status()


async def post_pr_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    installation_id: int,
) -> None:
    """Post a plain issue comment on a PR."""
    token = await get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={"body": body},
            timeout=30,
        )
        resp.raise_for_status()


class GitHubClient:
    """GitHub API client with retry logic and installation token caching."""

    def __init__(self, installation_id: int | None = None):
        self.installation_id = installation_id
        self._token: str | None = None
        self._token_expires: int = 0

    async def _get_headers(self) -> dict:
        if self.installation_id:
            if time.time() > self._token_expires - 60:
                self._token = await get_installation_token(self.installation_id)
                self._token_expires = int(time.time()) + 3600
            return {
                "Authorization": f"token {self._token}",
                "Accept": "application/vnd.github.v3+json",
            }
        return {
            "Authorization": f"Bearer {generate_jwt()}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = await self._get_headers()
        # Allow callers to override headers (e.g., for diff Accept)
        if "headers" in kwargs:
            merged = {**headers, **kwargs.pop("headers")}
        else:
            merged = headers

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(
                        method, url, headers=merged, timeout=30, **kwargs
                    )
                    if resp.status_code in (429, 503):
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return resp
            except httpx.RequestError as exc:
                last_exc = exc
                await asyncio.sleep(2 ** attempt)

        raise Exception(
            f"GitHub API failed after 3 retries: {url}"
        ) from last_exc

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = await self._request(
            "GET", url, headers={"Accept": "application/vnd.github.v3.diff"}
        )
        resp.raise_for_status()
        return resp.text

    async def post_pr_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        comments: list[dict],
    ) -> None:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        resp = await self._request(
            "POST",
            url,
            json={"body": body, "event": "COMMENT", "comments": comments},
        )
        resp.raise_for_status()

    async def post_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> None:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp = await self._request("POST", url, json={"body": body})
        resp.raise_for_status()

    async def get_public_pr_diff(self, pr_url: str) -> tuple[str, str, str]:
        return await get_public_pr_diff(pr_url)
