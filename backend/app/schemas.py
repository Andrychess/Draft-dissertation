from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import SessionStatus, UserRole, Verdict


# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# Users
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.teacher
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Groups
class GroupCreate(BaseModel):
    cipher: str
    name: str


class GroupResponse(BaseModel):
    cipher: str
    name: str

    model_config = {"from_attributes": True}


# Questions & Templates
class QuestionCreate(BaseModel):
    text: str
    correct_answer: str
    max_score: float = 10.0
    type: str = "open"


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    correct_answer: Optional[str] = None
    max_score: Optional[float] = None


class QuestionResponse(BaseModel):
    id: int
    template_id: int
    text: str
    type: str
    correct_answer: str
    max_score: float

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    name: str
    material_id: Optional[int] = None
    weight_relevance: float = 0.25
    weight_correctness: float = 0.35
    weight_normativity: float = 0.20
    weight_logic: float = 0.20


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    material_id: Optional[int] = None
    weight_relevance: Optional[float] = None
    weight_correctness: Optional[float] = None
    weight_normativity: Optional[float] = None
    weight_logic: Optional[float] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    created_by: int
    material_id: Optional[int]
    created_at: datetime
    weight_relevance: float = 0.25
    weight_correctness: float = 0.35
    weight_normativity: float = 0.20
    weight_logic: float = 0.20
    questions: List[QuestionResponse] = []

    model_config = {"from_attributes": True}


class TemplateListItem(BaseModel):
    id: int
    name: str
    created_by: int
    material_id: Optional[int]
    created_at: datetime
    weight_relevance: float = 0.25
    weight_correctness: float = 0.35
    weight_normativity: float = 0.20
    weight_logic: float = 0.20

    model_config = {"from_attributes": True}


# Sessions
class SessionCreate(BaseModel):
    name: str
    template_id: int
    group_ciphers: List[str] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SessionExtend(BaseModel):
    end_time: datetime


class SessionResponse(BaseModel):
    id: int
    name: str
    connection_code: str
    template_id: int
    created_by: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    status: SessionStatus

    model_config = {"from_attributes": True}


class SessionJoinRequest(BaseModel):
    connection_code: str
    student_name: str = ""
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    patronymic: Optional[str] = None
    group_cipher: Optional[str] = None
    device_fingerprint: Optional[str] = None


class SessionJoinResponse(BaseModel):
    session_id: int
    sheet_id: int
    session_name: str
    status: SessionStatus


# Answers
class AnswerSaveRequest(BaseModel):
    sheet_id: int
    question_id: int
    answer_text: str


class AnswerSubmitRequest(BaseModel):
    sheet_id: int


class AnswerSaveResponse(BaseModel):
    answer_id: int
    saved_at: datetime


# Results
class AICheckResultResponse(BaseModel):
    check_id: int
    sheet_id: int
    question_id: int
    score: float
    confidence: float
    verdict: Verdict
    explanation: str
    weaknesses: Optional[List[str]]
    strengths: Optional[List[str]]
    details: Optional[dict] = None
    model_version: Optional[str] = None
    checked_at: datetime
    corrected_score: Optional[float]
    approved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class StudentResultItem(BaseModel):
    question_id: int
    question_text: str
    max_score: float
    answer_text: Optional[str]
    submitted_at: Optional[datetime]
    score: Optional[float]
    confidence: Optional[float]
    verdict: Optional[str]
    explanation: Optional[str]
    weaknesses: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    details: Optional[dict] = None


class SystemLogResponse(BaseModel):
    id: int
    created_at: datetime
    user_id: Optional[int]
    action: str
    message: str
    ip_address: Optional[str]
    extra: Optional[dict] = None

    model_config = {"from_attributes": True}


class SystemSettingsUpdate(BaseModel):
    ai_timeout_sec: Optional[str] = None
    passing_threshold: Optional[str] = None
    confidence_threshold: Optional[str] = None


class ResultDetailResponse(BaseModel):
    sheet_id: int
    question_id: int
    student_name: str
    group_cipher: Optional[str]
    answer_text: Optional[str]
    submitted_at: Optional[datetime]
    ai_result: Optional[AICheckResultResponse]


class ResultApprove(BaseModel):
    pass


class ResultCorrect(BaseModel):
    corrected_score: float
    explanation: Optional[str] = None


class SessionResultRow(BaseModel):
    sheet_id: int
    student_name: str
    group_cipher: Optional[str]
    total_score: float
    max_score: float
    verdict: Optional[str]
