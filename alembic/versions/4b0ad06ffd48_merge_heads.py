"""merge heads

Revision ID: 4b0ad06ffd48
Revises: 32e85a4f15c0, b075b104e210
Create Date: 2025-09-07 14:59:39.826401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b0ad06ffd48'
down_revision: Union[str, None] = ('32e85a4f15c0', 'b075b104e210')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
