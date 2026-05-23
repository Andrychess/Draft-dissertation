from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"


class SessionStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    finished = "finished"


class Verdict(str, enum.Enum):
    passed = "passed"
    failed = "failed"
    review = "review"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.teacher)
    full_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    templates: Mapped[list[AssessmentTemplate]] = relationship(back_populates="creator")
    sessions: Mapped[list[Session]] = relationship(back_populates="creator")
    materials: Mapped[list[LectureMaterial]] = relationship(back_populates="uploader")


class StudyGroup(Base):
    __tablename__ = "study_groups"

    cipher: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class LectureMaterial(Base):
    __tablename__ = "lecture_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploader: Mapped[User] = relationship(back_populates="materials")
    templates: Mapped[list[AssessmentTemplate]] = relationship(back_populates="material")


class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    material_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecture_materials.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    weight_relevance: Mapped[float] = mapped_column(Float, default=0.25)
    weight_correctness: Mapped[float] = mapped_column(Float, default=0.35)
    weight_normativity: Mapped[float] = mapped_column(Float, default=0.20)
    weight_logic: Mapped[float] = mapped_column(Float, default=0.20)

    creator: Mapped[User] = relationship(back_populates="templates")
    material: Mapped[Optional[LectureMaterial]] = relationship(back_populates="templates")
    questions: Mapped[list[Question]] = relationship(back_populates="template", cascade="all, delete-orphan")
    sessions: Mapped[list[Session]] = relationship(back_populates="template")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("assessment_templates.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20), default="open")
    correct_answer: Mapped[str] = mapped_column(Text)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)

    template: Mapped[AssessmentTemplate] = relationship(back_populates="questions")
    answer_sheets: Mapped[list[AnswerSheet]] = relationship(back_populates="question")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    connection_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("assessment_templates.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.planned)

    template: Mapped[AssessmentTemplate] = relationship(back_populates="sessions")
    creator: Mapped[User] = relationship(back_populates="sessions")
    session_groups: Mapped[list[SessionGroup]] = relationship(back_populates="session", cascade="all, delete-orphan")
    answer_sheets: Mapped[list[AnswerSheet]] = relationship(back_populates="session")


class SessionGroup(Base):
    __tablename__ = "session_groups"

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    group_cipher: Mapped[str] = mapped_column(ForeignKey("study_groups.cipher"), primary_key=True)

    session: Mapped[Session] = relationship(back_populates="session_groups")
    group: Mapped[StudyGroup] = relationship()


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    answer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    answer_text: Mapped[str] = mapped_column(Text)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answer_sheet: Mapped[Optional[AnswerSheet]] = relationship(back_populates="student_answer")


class AnswerSheet(Base):
    __tablename__ = "answer_sheets"

    sheet_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    student_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    patronymic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    group_cipher: Mapped[Optional[str]] = mapped_column(ForeignKey("study_groups.cipher"), nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    answer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("student_answers.answer_id"), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[Session] = relationship(back_populates="answer_sheets")
    question: Mapped[Question] = relationship(back_populates="answer_sheets")
    group: Mapped[Optional[StudyGroup]] = relationship()
    student_answer: Mapped[Optional[StudentAnswer]] = relationship(back_populates="answer_sheet")
    ai_results: Mapped[list[AICheckResult]] = relationship(back_populates="answer_sheet")


class AICheckResult(Base):
    __tablename__ = "ai_check_results"

    check_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sheet_id: Mapped[int] = mapped_column()
    question_id: Mapped[int] = mapped_column()
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict))
    explanation: Mapped[str] = mapped_column(Text)
    weaknesses: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    strengths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    corrected_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["sheet_id", "question_id"],
            ["answer_sheets.sheet_id", "answer_sheets.question_id"],
        ),
    )

    answer_sheet: Mapped[AnswerSheet] = relationship(back_populates="ai_results")
    approver: Mapped[Optional[User]] = relationship()


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    user: Mapped[Optional[User]] = relationship()


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
