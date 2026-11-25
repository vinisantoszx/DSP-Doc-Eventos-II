"""adiciona campo andar em espaco

Revision ID: 8a8e4c68cb09
Revises: 0f19118b877f
Create Date: 2026-11-22 22:39:18.129928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8a8e4c68cb09'
down_revision: Union[str, Sequence[str], None] = '0f19118b877f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('espaco', sa.Column('andar', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('espaco', 'andar')
