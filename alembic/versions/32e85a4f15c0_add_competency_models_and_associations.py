"""Add competency models and associations

Revision ID: 32e85a4f15c0
Revises: fd286eb3f95f
Create Date: 2025-09-07 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '32e85a4f15c0'
down_revision: Union[str, None] = 'fd286eb3f95f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # competencies cədvəlini yarat (əgər yoxdursa)
    if 'competencies' not in tables:
        op.create_table('competencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_competencies_id'), 'competencies', ['id'], unique=False)
        op.create_index(op.f('ix_competencies_name'), 'competencies', ['name'], unique=False)
    
    # kpi_question_competency cədvəlini yarat (əgər yoxdursa və questions cədvəli mövcuddursa)
    if 'kpi_question_competency' not in tables and 'questions' in tables:
        op.create_table('kpi_question_competency',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'competency_id')
        )
    
    # degree360_question_competency cədvəlini yarat (əgər yoxdursa və degree360_questions cədvəli mövcuddursa)
    if 'degree360_question_competency' not in tables and 'degree360_questions' in tables:
        op.create_table('degree360_question_competency',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('competency_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['competency_id'], ['competencies.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['degree360_questions.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'competency_id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Check if tables exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # degree360_question_competency cədvəlini sil (əgər varsa)
    if 'degree360_question_competency' in tables:
        op.drop_table('degree360_question_competency')
    
    # kpi_question_competency cədvəlini sil (əgər varsa)
    if 'kpi_question_competency' in tables:
        op.drop_table('kpi_question_competency')
    
    # competencies cədvəlini sil (əgər varsa)
    if 'competencies' in tables:
        op.drop_index(op.f('ix_competencies_name'), table_name='competencies')
        op.drop_index(op.f('ix_competencies_id'), table_name='competencies')
        op.drop_table('competencies')