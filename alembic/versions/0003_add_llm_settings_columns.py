"""Add LLM settings columns to app_config.

Revision ID: 0003abcd5678
Revises: 0002abcd1234
Create Date: 2026-04-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "0003abcd5678"
down_revision: Union[str, None] = "0002abcd1234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_config", sa.Column("llm_api_key_encrypted", sa.String(), nullable=True))
    op.add_column("app_config", sa.Column("llm_ollama_base_url", sa.String(), nullable=True))
    op.add_column(
        "app_config",
        sa.Column("review_mode", sa.String(), nullable=False, server_default="exceptions"),
    )


def downgrade() -> None:
    op.drop_column("app_config", "review_mode")
    op.drop_column("app_config", "llm_ollama_base_url")
    op.drop_column("app_config", "llm_api_key_encrypted")
