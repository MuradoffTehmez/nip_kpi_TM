"""EvaluationStatus enum-u yenilendi

Revision ID: 3a9ea5c157d0
Revises: ab15f9cb8378
Create Date: 2025-09-07 13:09:31.251817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a9ea5c157d0'
down_revision: Union[str, None] = 'ab15f9cb8378'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # EvaluationStatus enum-unu yenilə
    # Köhnə dəyərləri sil
    op.execute("ALTER TYPE evaluationstatus RENAME TO evaluationstatus_old")
    # Yeni enum yarat
    op.execute("CREATE TYPE evaluationstatus AS ENUM ('GÖZLƏMƏDƏ', 'İŞÇİ DƏYƏRLƏNDİRDİ', 'RƏHBƏR DƏYƏRLƏNDİRDİ', 'YEKUNLAŞDIRILDI')")
    # Sütunu yeni enum ilə yenilə
    op.execute("ALTER TABLE evaluations ALTER COLUMN status TYPE evaluationstatus USING status::text::evaluationstatus")
    # Köhnə enum-u sil
    op.execute("DROP TYPE evaluationstatus_old")


def downgrade() -> None:
    """Downgrade schema."""
    # EvaluationStatus enum-unu köhnə halına qaytar
    # Köhnə dəyərləri sil
    op.execute("ALTER TYPE evaluationstatus RENAME TO evaluationstatus_old")
    # Köhnə enum yarat
    op.execute("CREATE TYPE evaluationstatus AS ENUM ('GÖZLƏMƏDƏ', 'TAMAMLANMIŞ')")
    # Sütunu köhnə enum ilə yenilə
    op.execute("ALTER TABLE evaluations ALTER COLUMN status TYPE evaluationstatus USING status::text::evaluationstatus")
    # Yeni enum-u sil
    op.execute("DROP TYPE evaluationstatus_old")
