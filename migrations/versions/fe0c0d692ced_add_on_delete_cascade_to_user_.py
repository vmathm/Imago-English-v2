"""Add ON DELETE CASCADE to user relationships

Revision ID: fe0c0d692ced
Revises: 655abf56a280
Create Date: 2026-02-04 19:23:32.101912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fe0c0d692ced'
down_revision: Union[str, Sequence[str], None] = '655abf56a280'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # flashcards.user_id -> users.id (CASCADE)
    op.drop_constraint("flashcards_user_id_fkey", "flashcards", type_="foreignkey")
    op.create_foreign_key(
        "flashcards_user_id_fkey",
        "flashcards",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Make timestamps timezone-aware
    op.alter_column(
        "user_audiobooks",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "user_audiobooks",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )

    # user_audiobooks.user_id -> users.id (CASCADE)
    op.drop_constraint("user_audiobooks_user_id_fkey", "user_audiobooks", type_="foreignkey")
    op.create_foreign_key(
        "user_audiobooks_user_id_fkey",
        "user_audiobooks",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # user_audiobooks.user_id -> users.id (no cascade)
    op.drop_constraint("user_audiobooks_user_id_fkey", "user_audiobooks", type_="foreignkey")
    op.create_foreign_key(
        "user_audiobooks_user_id_fkey",
        "user_audiobooks",
        "users",
        ["user_id"],
        ["id"],
    )

    # Revert timestamps
    op.alter_column(
        "user_audiobooks",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.alter_column(
        "user_audiobooks",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )

    # flashcards.user_id -> users.id (no cascade)
    op.drop_constraint("flashcards_user_id_fkey", "flashcards", type_="foreignkey")
    op.create_foreign_key(
        "flashcards_user_id_fkey",
        "flashcards",
        "users",
        ["user_id"],
        ["id"],
    )
