"""plan_items cedvelini elave et

Revision ID: 60379e133368
Revises: 3a9ea5c157d0
Create Date: 2025-09-07 13:24:05.295869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60379e133368'
down_revision: Union[str, None] = '3a9ea5c157d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # development_plans cədvəlini yaradırıq (əgər yoxdursa)
    op.create_table('development_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('evaluation_id', sa.Integer(), nullable=False),
    sa.Column('manager_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
    sa.ForeignKeyConstraint(['manager_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_development_plans_id'), 'development_plans', ['id'], unique=False)
    
    # plan_items cədvəlini yaradırıq
    op.create_table('plan_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plan_id', sa.Integer(), nullable=False),
    sa.Column('goal', sa.String(), nullable=False),
    sa.Column('actions_to_take', sa.String(), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), server_default=sa.text('false'), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['development_plans.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_items_id'), 'plan_items', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # plan_items cədvəlini silirik
    op.drop_index(op.f('ix_plan_items_id'), table_name='plan_items')
    op.drop_table('plan_items')
    
    # development_plans cədvəlini silirik
    op.drop_index(op.f('ix_development_plans_id'), table_name='development_plans')
    op.drop_table('development_plans')
