from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ── Auth & User Schemas ────────────────────────────────────────────────────────
class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    full_name: Optional[str] = Field(default=None, max_length=100)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseSchema


# ── Topic Validation Schemas ───────────────────────────────────────────────────
class TopicValidationRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Research topic to validate")


class TopicValidationResponse(BaseModel):
    valid: bool
    reason: str = ""


# ── Research Pipeline Schemas ──────────────────────────────────────────────────
class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Research subject or question")
    save_to_history: bool = Field(default=True, description="Whether to save the final report to DB")


class ResearchResponse(BaseModel):
    id: Optional[int] = None
    topic: str
    report: str
    critique: Optional[str] = None
    score: Optional[int] = None
    sources: List[str] = []
    chart_data: Dict[str, Any] = {}
    sub_queries: List[str] = []
    iterations: int = 1
    created_at: Optional[datetime] = None


# ── Reports & History Schemas ──────────────────────────────────────────────────
class ReportListItem(BaseModel):
    id: int
    topic: str
    score: Optional[int] = None
    iterations: int = 1
    status: str = "completed"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportDetailResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    topic: str
    report_markdown: str
    critique: Optional[str] = None
    score: Optional[int] = None
    sources: List[str] = []
    chart_data: Dict[str, Any] = {}
    sub_queries: List[str] = []
    iterations: int = 1
    status: str = "completed"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
