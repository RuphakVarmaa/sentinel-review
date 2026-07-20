from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("/")
async def list_repos():
    """List repositories connected via GitHub App installation.

    Returns an empty list until the user connects a GitHub account.
    """
    return {
        "repos": [],
        "message": "Connect your GitHub account to see repos",
    }


@router.get("/{owner}/{repo}/reviews")
async def get_repo_reviews(owner: str, repo: str):
    """List all reviews for a specific repository.

    Returns an empty list until reviews are persisted to the database.
    """
    return {
        "reviews": [],
        "owner": owner,
        "repo": repo,
    }
