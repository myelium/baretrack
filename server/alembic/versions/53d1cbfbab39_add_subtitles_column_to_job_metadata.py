"""Add subtitles column to job_metadata

Revision ID: 53d1cbfbab39
Revises: 51e746a35710
Create Date: 2026-03-31 02:00:30.943257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '53d1cbfbab39'
down_revision: Union[str, Sequence[str], None] = '51e746a35710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_metadata', sa.Column('subtitles', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_metadata', 'subtitles')
