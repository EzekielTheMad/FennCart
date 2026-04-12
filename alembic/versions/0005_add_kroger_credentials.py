"""Add encrypted Kroger credential columns to app_config.

Revision ID: 0005abcd0001
Revises: 0004abcd9012
Create Date: 2026-04-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "0005abcd0001"
down_revision: Union[str, None] = "0004abcd9012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("app_config", sa.Column("kroger_client_id_encrypted", sa.String(), nullable=True))
    op.add_column("app_config", sa.Column("kroger_client_secret_encrypted", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_config", "kroger_client_secret_encrypted")
    op.drop_column("app_config", "kroger_client_id_encrypted")
