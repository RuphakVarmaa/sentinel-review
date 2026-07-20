from pydantic import BaseModel
from enum import Enum
from typing import Optional
from uuid import UUID


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Category(str, Enum):
    security = "security"
    logic = "logic"
    performance = "performance"
    style = "style"
    maintainability = "maintainability"
    accessibility = "accessibility"


class Finding(BaseModel):
    id: UUID
    review_id: UUID
    category: Category
    severity: Severity
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    title: str
    explanation: str
    suggested_fix: Optional[str] = None
    why_it_matters: Optional[str] = None
    cwe_id: Optional[str] = None
    user_feedback: Optional[str] = None

    class Config:
        use_enum_values = True


class FindingCreate(BaseModel):
    category: Category
    severity: Severity
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    title: str
    explanation: str
    suggested_fix: Optional[str] = None
    why_it_matters: Optional[str] = None
    cwe_id: Optional[str] = None

    class Config:
        use_enum_values = True


class LLMFinding(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    title: Optional[str] = None
    explanation: Optional[str] = None
    suggested_fix: Optional[str] = None
    why_it_matters: Optional[str] = None
    cwe_id: Optional[str] = None
