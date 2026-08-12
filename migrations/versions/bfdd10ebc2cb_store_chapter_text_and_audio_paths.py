"""store chapter text and audio paths

Revision ID: bfdd10ebc2cb
Revises: 2643380990e8
Create Date: 2026-08-11 14:59:41.762443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfdd10ebc2cb'
down_revision: Union[str, Sequence[str], None] = '2643380990e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing chapter rows use the old storage format.
    # This feature is still in development, so discard them.
    op.execute("DELETE FROM chapters")

    op.add_column(
        "chapters",
        sa.Column(
            "text_path",
            sa.String(length=500),
            nullable=False,
        ),
    )

    op.add_column(
        "chapters",
        sa.Column(
            "audio_path",
            sa.String(length=500),
            nullable=False,
        ),
    )

    op.drop_column("chapters", "text_content")
    op.drop_column("chapters", "audio_object_name")

def downgrade() -> None:
    op.execute("DELETE FROM chapters")

    op.add_column(
        "chapters",
        sa.Column(
            "audio_object_name",
            sa.String(length=500),
            nullable=False,
        ),
    )

    op.add_column(
        "chapters",
        sa.Column(
            "text_content",
            sa.Text(),
            nullable=False,
        ),
    )

    op.drop_column("chapters", "audio_path")
    op.drop_column("chapters", "text_path")