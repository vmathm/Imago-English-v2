from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c5c89896310"
down_revision: Union[str, Sequence[str], None] = "86075a25d4f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chapters",
        sa.Column(
            "activity_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column(
        "chapters",
        "activity_enabled",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "chapters",
        "activity_enabled",
    )