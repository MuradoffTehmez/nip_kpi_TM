"""Yeni bildiris ve Ferdi Inkisaf Plani cedvellerini elave et

Revision ID: ab15f9cb8378
Revises: 5b5ac4427a71
Create Date: 2025-09-07 13:02:24.423055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab15f9cb8378'
down_revision: Union[str, None] = '5b5ac4427a71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # notifications cədvəli
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)

    # development_plans cədvəli
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

    # plan_items cədvəli
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
    # cədvəlləri sil
    op.drop_index(op.f('ix_plan_items_id'), table_name='plan_items')
    op.drop_table('plan_items')
    
    op.drop_index(op.f('ix_development_plans_id'), table_name='development_plans')
    op.drop_table('development_plans')
    
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
