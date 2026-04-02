"""Expand job_metadata for library queries

Revision ID: b66f7f67ead0
Revises: 0864f77e172e
Create Date: 2026-03-30 05:08:10.006046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b66f7f67ead0'
down_revision: Union[str, Sequence[str], None] = '0864f77e172e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_metadata', sa.Column('url', sa.String(length=512), nullable=True))
    op.add_column('job_metadata', sa.Column('mode', sa.String(length=20), nullable=True))
    op.add_column('job_metadata', sa.Column('languages', sa.Text(), nullable=True))
    op.add_column('job_metadata', sa.Column('thumbnail', sa.String(length=512), nullable=True))
    op.add_column('job_metadata', sa.Column('channel', sa.String(length=255), nullable=True))
    op.add_column('job_metadata', sa.Column('upload_date', sa.String(length=20), nullable=True))
    op.add_column('job_metadata', sa.Column('categories', sa.Text(), nullable=True))
    op.add_column('job_metadata', sa.Column('tags', sa.Text(), nullable=True))
    op.add_column('job_metadata', sa.Column('finished_at', sa.String(length=30), nullable=True))
    op.add_column('job_metadata', sa.Column('audio_duration', sa.Float(), nullable=True))
    op.add_column('job_metadata', sa.Column('language_detected', sa.String(length=10), nullable=True))
    op.add_column('job_metadata', sa.Column('status', sa.String(length=20), nullable=True))
    op.add_column('job_metadata', sa.Column('added_by', sa.String(length=255), nullable=True))
    op.add_column('job_metadata', sa.Column('added_by_id', sa.String(length=255), nullable=True))
    op.add_column('job_metadata', sa.Column('error', sa.Text(), nullable=True))
    op.add_column('job_metadata', sa.Column('file_size_bytes', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_metadata', 'file_size_bytes')
    op.drop_column('job_metadata', 'error')
    op.drop_column('job_metadata', 'added_by_id')
    op.drop_column('job_metadata', 'added_by')
    op.drop_column('job_metadata', 'status')
    op.drop_column('job_metadata', 'language_detected')
    op.drop_column('job_metadata', 'audio_duration')
    op.drop_column('job_metadata', 'finished_at')
    op.drop_column('job_metadata', 'tags')
    op.drop_column('job_metadata', 'categories')
    op.drop_column('job_metadata', 'upload_date')
    op.drop_column('job_metadata', 'channel')
    op.drop_column('job_metadata', 'thumbnail')
    op.drop_column('job_metadata', 'languages')
    op.drop_column('job_metadata', 'mode')
    op.drop_column('job_metadata', 'url')
