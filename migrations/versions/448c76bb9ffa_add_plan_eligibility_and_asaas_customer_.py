"""add plan eligibility and asaas customer id

Revision ID: 448c76bb9ffa
Revises: 2a72f4902778
Create Date: 2026-04-08 14:12:10.740708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '448c76bb9ffa'
down_revision: Union[str, Sequence[str], None] = '2a72f4902778'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plan_students',
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('plan_id', 'user_id')
    )

    op.add_column(
        'plans',
        sa.Column(
            'available_to_all_students',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )
    )
    op.alter_column('plans', 'available_to_all_students', server_default=None)

    op.create_index(
        op.f('ix_users_asaas_customer_id'),
        'users',
        ['asaas_customer_id'],
        unique=True
    )

    op.drop_column('users', 'cpf_cnpj')


def downgrade() -> None:
    op.add_column(
        'users',
        sa.Column('cpf_cnpj', sa.String(length=18), nullable=True)
    )

    op.drop_index(op.f('ix_users_asaas_customer_id'), table_name='users')

    op.drop_column('plans', 'available_to_all_students')

    op.drop_table('plan_students')