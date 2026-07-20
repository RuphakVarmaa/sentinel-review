from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.finding import Finding, Severity


class ReviewSource(str, Enum):
    web = "web"
    api = "api"
    github_app = "github_app"
    ci = "ci"


class ReviewStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class FindingCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class Review(BaseModel):
    id: UUID
    share_id: Optional[str] = None
    user_id: Optional[UUID] = None
    source: ReviewSource
    repo_full_name: Optional[str] = None
    pr_number: Optional[int] = None
    diff_text: str
    diff_line_count: int
    overall_severity: Optional[Severity] = None
    finding_counts: FindingCounts = Field(default_factory=FindingCounts)
    model_used: str
    latency_ms: Optional[int] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    findings: List[Finding] = []

    class Config:
        use_enum_values = True


class ReviewRequest(BaseModel):
    diff: Optional[str] = Field(None, max_length=100000)
    context: Optional[str] = Field(None, max_length=500)
    source: ReviewSource = ReviewSource.web
    pr_url: Optional[str] = None

    class Config:
        use_enum_values = True


class ReviewResponse(BaseModel):
    review_id: UUID
    overall_severity: Optional[Severity] = None
    finding_counts: FindingCounts
    model_used: str
    latency_ms: Optional[int] = None
    findings: List
    share_id: Optional[str] = None

    class Config:
        use_enum_values = True
