"""Add job_metadata table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_metadata",
        sa.Column("job_id", sa.String(255), primary_key=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("artist", sa.String(255), nullable=True),
        sa.Column("view_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("analysis_text", sa.Text, nullable=True),
        sa.Column("analysis_song_info", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("job_metadata")
