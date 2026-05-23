"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "teacher", name="userrole"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
    )
    op.create_table(
        "study_groups",
        sa.Column("cipher", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_table(
        "lecture_materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "assessment_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("lecture_materials.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("assessment_templates.id", ondelete="CASCADE")),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), server_default="open"),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("max_score", sa.Float(), server_default="10"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("connection_code", sa.String(20), nullable=False, unique=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("assessment_templates.id")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("planned", "active", "finished", name="sessionstatus"), nullable=False),
    )
    op.create_table(
        "session_groups",
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_cipher", sa.String(50), sa.ForeignKey("study_groups.cipher"), primary_key=True),
    )
    op.create_table(
        "student_answers",
        sa.Column("answer_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "answer_sheets",
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id")),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("group_cipher", sa.String(50), sa.ForeignKey("study_groups.cipher"), nullable=True),
        sa.Column("answer_id", sa.Integer(), sa.ForeignKey("student_answers.answer_id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("sheet_id", "question_id"),
    )
    op.create_table(
        "ai_check_results",
        sa.Column("check_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sheet_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verdict", sa.Enum("passed", "failed", "review", name="verdict"), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("corrected_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["sheet_id", "question_id"],
            ["answer_sheets.sheet_id", "answer_sheets.question_id"],
        ),
    )


def downgrade() -> None:
    op.drop_table("ai_check_results")
    op.drop_table("answer_sheets")
    op.drop_table("student_answers")
    op.drop_table("session_groups")
    op.drop_table("sessions")
    op.drop_table("questions")
    op.drop_table("assessment_templates")
    op.drop_table("lecture_materials")
    op.drop_table("study_groups")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS verdict")
