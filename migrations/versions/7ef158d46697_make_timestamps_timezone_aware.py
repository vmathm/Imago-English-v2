"""Make timestamps timezone-aware

Revision ID: 7ef158d46697
Revises: fe0c0d692ced
Create Date: 2026-02-11 13:20:22.623406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7ef158d46697'
down_revision: Union[str, Sequence[str], None] = 'fe0c0d692ced'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # calendar_settings: TIMESTAMP -> TIMESTAMPTZ (treat existing as UTC)
    op.alter_column(
        "calendar_settings",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "calendar_settings",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        nullable=False,
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )

    # flashcards: TIMESTAMP -> TIMESTAMPTZ (treat existing as UTC)
    op.alter_column(
        "flashcards",
        "last_review",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="last_review AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "flashcards",
        "next_review",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="next_review AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "flashcards",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )

    # user_audiobooks already timestamptz; keep as-is (just enforcing non-null)
    op.alter_column(
        "user_audiobooks",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "user_audiobooks",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "user_audiobooks",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "user_audiobooks",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )

    op.alter_column(
        "flashcards",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "flashcards",
        "next_review",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
        postgresql_using="next_review AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "flashcards",
        "last_review",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
        postgresql_using="last_review AT TIME ZONE 'UTC'",
    )

    op.alter_column(
        "calendar_settings",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        postgresql_using="updated_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "calendar_settings",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        nullable=True,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )

    # ### end Alembic commands ###
