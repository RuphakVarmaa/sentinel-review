from pydantic import BaseModel
from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserPlan(str, Enum):
    free = "free"
    pro = "pro"


class User(BaseModel):
    id: UUID
    github_id: Optional[str] = None
    email: Optional[str] = None
    plan: UserPlan = UserPlan.free
    api_key: Optional[str] = None
    reviews_this_month: int = 0
    created_at: datetime

    class Config:
        use_enum_values = True


class UserCreate(BaseModel):
    github_id: Optional[str] = None
    email: Optional[str] = None
    plan: UserPlan = UserPlan.free
    api_key: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    plan: Optional[UserPlan] = None
    api_key: Optional[str] = None
    reviews_this_month: Optional[int] = None
