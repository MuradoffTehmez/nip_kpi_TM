"""Kohne performance ve indicator cedvellerini sil

Revision ID: 5b5ac4427a71
Revises: dcc0a96d5c1a
Create Date: 2025-09-07 12:52:45.276866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b5ac4427a71'
down_revision: Union[str, None] = 'dcc0a96d5c1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # performance cədvəlini sil
    op.drop_table('performance')
    # indicator cədvəlini sil
    op.drop_table('indicator')


def downgrade() -> None:
    """Downgrade schema."""
    # Bu geri dönüş mümkün deyil, çünki cədvəllər və məlumatlar silinib
    pass
