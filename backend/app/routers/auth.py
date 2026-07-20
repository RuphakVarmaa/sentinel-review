from fastapi import APIRouter, HTTPException
from app.config import settings
import httpx
import secrets
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github")
async def github_oauth_redirect():
    """Return the GitHub OAuth authorization URL for the frontend to redirect to."""
    params = f"client_id={settings.GITHUB_CLIENT_ID}&scope=read:user,user:email"
    return {"redirect_url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/github/callback")
async def github_oauth_callback(code: str):
    """Exchange a GitHub OAuth code for an access token and return user info.

    In a full implementation this would upsert the user in the database
    and issue a signed JWT session token. For now it returns the GitHub
    user profile and a generated API key.
    """
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        token_data = resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(400, "OAuth failed: no access token returned from GitHub")

    # Fetch user profile
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
            timeout=30,
        )
        user_data = resp.json()

    # Generate a scoped API key for the user
    api_key = f"sk-sentinel-{secrets.token_urlsafe(32)}"

    return {
        "user": {
            "github_id": str(user_data.get("id")),
            "login": user_data.get("login"),
            "email": user_data.get("email"),
            "avatar_url": user_data.get("avatar_url"),
        },
        "api_key": api_key,
        "message": "Store this API key securely. It won't be shown again.",
    }


@router.post("/api-key/generate")
async def generate_api_key():
    """Generate a new Sentinel API key.

    In production this should be gated behind authentication.
    """
    api_key = f"sk-sentinel-{secrets.token_urlsafe(32)}"
    return {"api_key": api_key}
