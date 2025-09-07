"""360 derece qiymetlendirme modellerini elave et

Revision ID: fd286eb3f95f
Revises: c6d5daedd076
Create Date: 2025-09-07 13:38:57.876028

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fd286eb3f95f'
down_revision: Union[str, None] = 'c6d5daedd076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Degree360ParticipantRole enum yarat (əgər yoxdursa)
    try:
        # Check if enum already exists
        result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'degree360participantrole'")).fetchone()
        if not result:
            op.execute("CREATE TYPE degree360participantrole AS ENUM ('SELF', 'MANAGER', 'PEER', 'SUBORDINATE', 'CUSTOMER')")
    except Exception as e:
        # If enum already exists, continue
        pass
    
    # degree360_sessions cədvəlini yarat (əgər yoxdursa)
    if 'degree360_sessions' not in tables:
        op.create_table('degree360_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('evaluated_user_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_user_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['evaluated_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['evaluator_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_degree360_sessions_id'), 'degree360_sessions', ['id'], unique=False)
    
    # degree360_questions cədvəlini yarat (əgər yoxdursa)
    if 'degree360_questions' not in tables:
        op.create_table('degree360_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['degree360_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_degree360_questions_id'), 'degree360_questions', ['id'], unique=False)
    
    # degree360_participants cədvəlini yarat (əgər yoxdursa)
    if 'degree360_participants' not in tables:
        op.create_table('degree360_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('evaluator_user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('SELF', 'MANAGER', 'PEER', 'SUBORDINATE', 'CUSTOMER', name='degree360participantrole'), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['evaluator_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['degree360_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_degree360_participants_id'), 'degree360_participants', ['id'], unique=False)
    
    # degree360_answers cədvəlini yarat (əgər yoxdursa)
    if 'degree360_answers' not in tables:
        op.create_table('degree360_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('participant_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['participant_id'], ['degree360_participants.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['degree360_questions.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_degree360_answers_id'), 'degree360_answers', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if tables exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # degree360_answers cədvəlini sil (əgər varsa)
    if 'degree360_answers' in tables:
        op.drop_index(op.f('ix_degree360_answers_id'), table_name='degree360_answers')
        op.drop_table('degree360_answers')
    
    # degree360_participants cədvəlini sil (əgər varsa)
    if 'degree360_participants' in tables:
        op.drop_index(op.f('ix_degree360_participants_id'), table_name='degree360_participants')
        op.drop_table('degree360_participants')
    
    # degree360_questions cədvəlini sil (əgər varsa)
    if 'degree360_questions' in tables:
        op.drop_index(op.f('ix_degree360_questions_id'), table_name='degree360_questions')
        op.drop_table('degree360_questions')
    
    # degree360_sessions cədvəlini sil (əgər varsa)
    if 'degree360_sessions' in tables:
        op.drop_index(op.f('ix_degree360_sessions_id'), table_name='degree360_sessions')
        op.drop_table('degree360_sessions')
    
    # Degree360ParticipantRole enum-u sil (əgər mövcuddursa)
    try:
        # Check if enum exists before dropping
        result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'degree360participantrole'")).fetchone()
        if result:
            op.execute("DROP TYPE degree360participantrole")
    except:
        pass  # Enum mövcud deyil
