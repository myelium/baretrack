"""Add app_config table

Revision ID: 0864f77e172e
Revises: b2c3d4e5f6a7
Create Date: 2026-03-30 05:07:05.105716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0864f77e172e'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('app_config',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )


def downgrade() -> None:
    op.drop_table('app_config')
