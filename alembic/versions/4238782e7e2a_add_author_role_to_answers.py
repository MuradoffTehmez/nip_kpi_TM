"""add_author_role_to_answers

Revision ID: 4238782e7e2a
Revises: fd286eb3f95f
Create Date: 2025-09-07 13:57:23.544185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4238782e7e2a'
down_revision: Union[str, None] = 'fd286eb3f95f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns in answers table
    existing_columns = [col['name'] for col in inspector.get_columns('answers')]
    
    # Add author_role column to answers table (əgər yoxdursa)
    if 'author_role' not in existing_columns:
        op.add_column('answers', sa.Column('author_role', sa.String(20), nullable=False, server_default='employee'))


def downgrade() -> None:
    """Downgrade schema."""
    # Check if column exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns in answers table
    existing_columns = [col['name'] for col in inspector.get_columns('answers')]
    
    # Remove author_role column from answers table (əgər varsa)
    if 'author_role' in existing_columns:
        op.drop_column('answers', 'author_role')
