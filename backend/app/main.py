from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import review, webhook, auth, repos, shares

app = FastAPI(
    title="Sentinel Review API",
    description="LLM-powered code review platform. Paste a diff, get instant AI review.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review.router)
app.include_router(webhook.router)
app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(shares.router)


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    return {
        "name": "Sentinel Review API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }
