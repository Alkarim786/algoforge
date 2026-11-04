"""user roles

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=10), server_default='student', nullable=False))
    op.create_check_constraint(op.f('ck_users_role'), 'users', "role IN ('student', 'admin')")


def downgrade() -> None:
    op.drop_constraint(op.f('ck_users_role'), 'users', type_='check')
    op.drop_column('users', 'role')
