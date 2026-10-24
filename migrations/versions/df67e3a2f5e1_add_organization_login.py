"""add organization login

Revision ID: df67e3a2f5e1
Revises: 07ae243a488f
Create Date: 2026-10-24 19:37:22.512754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df67e3a2f5e1'
down_revision: Union[str, Sequence[str], None] = '07ae243a488f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organization', sa.Column('email', sa.String(length=320), nullable=True))
    op.add_column('organization', sa.Column('hashed_password', sa.String(length=255), nullable=True))
    op.create_unique_constraint('organization_email_key', 'organization', ['email'])


def downgrade() -> None:
    op.drop_constraint('organization_email_key', 'organization', type_='unique')
    op.drop_column('organization', 'hashed_password')
    op.drop_column('organization', 'email')
