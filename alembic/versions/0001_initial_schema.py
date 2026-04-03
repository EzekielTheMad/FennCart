"""initial schema: app_config and oauth_tokens

Revision ID: 0001
Revises:
Create Date: 2026-04-02 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wizard_step", sa.String(), nullable=False, server_default="start"),
        sa.Column("wizard_complete", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("store_id", sa.String(), nullable=True),
        sa.Column("store_name", sa.String(), nullable=True),
        sa.Column("store_zip", sa.String(), nullable=True),
        sa.Column("llm_provider", sa.String(), nullable=False, server_default="anthropic"),
        sa.Column("llm_model", sa.String(), nullable=False, server_default="claude-3-haiku-20240307"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("access_token_encrypted", sa.String(), nullable=False, server_default=""),
        sa.Column("refresh_token_encrypted", sa.String(), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("token_type", sa.String(), nullable=False, server_default="Bearer"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("oauth_tokens")
    op.drop_table("app_config")
