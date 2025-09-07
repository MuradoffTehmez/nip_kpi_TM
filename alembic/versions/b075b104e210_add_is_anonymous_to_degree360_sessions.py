"""add_is_anonymous_to_degree360_sessions

Revision ID: b075b104e210
Revises: 4238782e7e2a
Create Date: 2025-09-07 14:01:38.445895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b075b104e210'
down_revision: Union[str, None] = '4238782e7e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists before trying to get columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Add is_anonymous column to degree360_sessions table (əgər cədvəl varsa və sütun yoxdursa)
    if 'degree360_sessions' in tables:
        # Get existing columns in degree360_sessions table
        existing_columns = [col['name'] for col in inspector.get_columns('degree360_sessions')]
        
        if 'is_anonymous' not in existing_columns:
            op.add_column('degree360_sessions', sa.Column('is_anonymous', sa.Boolean(), nullable=True, server_default='true'))
            # Update existing rows to have is_anonymous = true
            op.execute("UPDATE degree360_sessions SET is_anonymous = true WHERE is_anonymous IS NULL")
            # Make the column NOT NULL
            op.alter_column('degree360_sessions', 'is_anonymous', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists before trying to get columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Remove is_anonymous column from degree360_sessions table (əgər cədvəl və sütun varsa)
    if 'degree360_sessions' in tables:
        # Get existing columns in degree360_sessions table
        existing_columns = [col['name'] for col in inspector.get_columns('degree360_sessions')]
        
        if 'is_anonymous' in existing_columns:
            op.drop_column('degree360_sessions', 'is_anonymous')
