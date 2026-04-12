"""Add parsed items and contradictions JSON columns to receipt_uploads.

Revision ID: 0006abcd0001
Revises: 0005abcd0001
Create Date: 2026-04-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "0006abcd0001"
down_revision: Union[str, None] = "0005abcd0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("receipt_uploads", sa.Column("parsed_items_json", sa.String(), nullable=True))
    op.add_column("receipt_uploads", sa.Column("contradictions_json", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("receipt_uploads", "contradictions_json")
    op.drop_column("receipt_uploads", "parsed_items_json")
