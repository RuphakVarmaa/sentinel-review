from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sentinel.db"
    REDIS_URL: str = "redis://localhost:6379"

    # AWS Bedrock credentials
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Bedrock model IDs (cross-region inference profiles)
    BEDROCK_MODEL_SONNET: str = "us.anthropic.claude-sonnet-4-6"
    BEDROCK_MODEL_HAIKU: str = "us.anthropic.claude-haiku-4-5-20251001"

    # GitHub App
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY: str = ""
    GITHUB_WEBHOOK_SECRET: str = "dev-secret"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    JWT_SECRET: str = "dev-jwt-secret-change-in-production"
    ENVIRONMENT: str = "production"
    CORS_ORIGINS: List[str] = [
        "https://sentinel-review.vercel.app",
        "http://localhost:3000",
    ]
    FREE_REVIEWS_PER_DAY: int = 5
    REVIEW_TIMEOUT_SECONDS: int = 45

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
