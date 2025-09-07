"""plan_items-e progress ve status saheleri elave et, plan_item_comments cedvelini yarat

Revision ID: c6d5daedd076
Revises: 60379e133368
Create Date: 2025-09-07 13:26:31.108996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6d5daedd076'
down_revision: Union[str, None] = '60379e133368'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # plan_items cədvəlinə progress və status sütunlarını əlavə edirik
    op.add_column('plan_items', sa.Column('progress', sa.Integer(), nullable=True))
    op.add_column('plan_items', sa.Column('status', sa.String(), nullable=True))
    
    # plan_item_comments cədvəlini yaradırıq
    op.create_table('plan_item_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('comment_text', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['item_id'], ['plan_items.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_item_comments_id'), 'plan_item_comments', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # plan_item_comments cədvəlini silirik
    op.drop_index(op.f('ix_plan_item_comments_id'), table_name='plan_item_comments')
    op.drop_table('plan_item_comments')
    
    # plan_items cədvəlindən progress və status sütunlarını silirik
    op.drop_column('plan_items', 'status')
    op.drop_column('plan_items', 'progress')
