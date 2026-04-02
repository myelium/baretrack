"""Add lyrics column to job_metadata

Revision ID: 51e746a35710
Revises: b66f7f67ead0
Create Date: 2026-03-30 20:03:49.502003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '51e746a35710'
down_revision: Union[str, Sequence[str], None] = 'b66f7f67ead0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_metadata', sa.Column('lyrics', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_metadata', 'lyrics')
