"""dissertation chapter 2 fields

Revision ID: 002
Revises: 001
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assessment_templates", sa.Column("weight_relevance", sa.Float(), server_default="0.25"))
    op.add_column("assessment_templates", sa.Column("weight_correctness", sa.Float(), server_default="0.35"))
    op.add_column("assessment_templates", sa.Column("weight_normativity", sa.Float(), server_default="0.20"))
    op.add_column("assessment_templates", sa.Column("weight_logic", sa.Float(), server_default="0.20"))

    op.add_column("answer_sheets", sa.Column("last_name", sa.String(100), nullable=True))
    op.add_column("answer_sheets", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("answer_sheets", sa.Column("patronymic", sa.String(100), nullable=True))
    op.add_column("answer_sheets", sa.Column("device_fingerprint", sa.String(128), nullable=True))

    op.add_column("ai_check_results", sa.Column("details", sa.JSON(), nullable=True))
    op.add_column("ai_check_results", sa.Column("model_version", sa.String(128), nullable=True))

    op.create_table(
        "system_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
    )
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.execute(
        "INSERT INTO system_settings (key, value) VALUES "
        "('ai_timeout_sec', '60'), ('passing_threshold', '0.6'), ('confidence_threshold', '0.7')"
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("system_logs")
    op.drop_column("ai_check_results", "model_version")
    op.drop_column("ai_check_results", "details")
    op.drop_column("answer_sheets", "device_fingerprint")
    op.drop_column("answer_sheets", "patronymic")
    op.drop_column("answer_sheets", "first_name")
    op.drop_column("answer_sheets", "last_name")
    op.drop_column("assessment_templates", "weight_logic")
    op.drop_column("assessment_templates", "weight_normativity")
    op.drop_column("assessment_templates", "weight_correctness")
    op.drop_column("assessment_templates", "weight_relevance")
