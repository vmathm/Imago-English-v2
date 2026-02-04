"""Widen users columns

Revision ID: 655abf56a280
Revises: d58c6ea98a28
Create Date: 2026-01-28 14:50:54.583967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '655abf56a280'
down_revision: Union[str, Sequence[str], None] = 'd58c6ea98a28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users", "name",
        existing_type=sa.VARCHAR(length=15),
        type_=sa.VARCHAR(length=120),
        existing_nullable=False,
    )

    op.alter_column(
        "users", "user_name",
        existing_type=sa.VARCHAR(length=20),
        type_=sa.VARCHAR(length=50),
        existing_nullable=True,
    )

    op.alter_column(
        "users", "phone",
        existing_type=sa.VARCHAR(length=15),
        type_=sa.VARCHAR(length=25),
        existing_nullable=True,
    )

    op.alter_column(
        "users", "profilepic",
        existing_type=sa.VARCHAR(length=300),
        type_=sa.Text(),
        existing_nullable=False,
        existing_server_default=sa.text("'none'::character varying"),
    )




def downgrade() -> None:

    op.alter_column(
        "users", "profilepic",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=300),
        existing_nullable=False,
        existing_server_default=sa.text("'none'::character varying"),
    )

    op.alter_column(
        "users", "phone",
        existing_type=sa.VARCHAR(length=25),
        type_=sa.VARCHAR(length=15),
        existing_nullable=True,
    )

    op.alter_column(
        "users", "user_name",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.VARCHAR(length=20),
        existing_nullable=True,
    )

    op.alter_column(
        "users", "name",
        existing_type=sa.VARCHAR(length=120),
        type_=sa.VARCHAR(length=15),
        existing_nullable=False,
    )
