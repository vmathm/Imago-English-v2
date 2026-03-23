"""add tenant owner

Revision ID: 2cbde5ec05be
Revises: e29659638702
Create Date: 2026-03-23 20:59:21.788657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cbde5ec05be'
down_revision: Union[str, Sequence[str], None] = 'e29659638702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('owner_user_id', sa.String(length=50), nullable=False))
    op.create_unique_constraint(
        'uq_tenants_owner_user_id',
        'tenants',
        ['owner_user_id']
    )
    op.create_foreign_key(
        'fk_tenants_owner_user_id',
        'tenants',
        'users',
        ['owner_user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_tenants_owner_user_id', 'tenants', type_='foreignkey')
    op.drop_constraint('uq_tenants_owner_user_id', 'tenants', type_='unique')
    op.drop_column('tenants', 'owner_user_id')