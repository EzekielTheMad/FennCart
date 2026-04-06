"""Create preference_entries and receipt_uploads tables.

Revision ID: 0004abcd9012
Revises: 0003abcd5678
Create Date: 2026-04-06 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0004abcd9012"
down_revision: Union[str, None] = "0003abcd5678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "preference_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_category", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("purchase_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_category", "brand", "product_name", name="uq_pref_category_brand_product"),
    )
    op.create_index(
        "ix_preference_entries_product_category",
        "preference_entries",
        ["product_category"],
    )

    op.create_table(
        "receipt_uploads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("items_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_confirmed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parse_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("parse_warnings", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("receipt_uploads")
    op.drop_index("ix_preference_entries_product_category", table_name="preference_entries")
    op.drop_table("preference_entries")
