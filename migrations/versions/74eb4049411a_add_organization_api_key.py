"""add organization api key

Revision ID: 74eb4049411a
Revises: df67e3a2f5e1
Create Date: 2026-10-25 00:45:39.836129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74eb4049411a'
down_revision: Union[str, Sequence[str], None] = 'df67e3a2f5e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organization', sa.Column('api_key_hash', sa.String(length=64), nullable=True))
    op.add_column('organization', sa.Column('api_key_hint', sa.String(length=8), nullable=True))
    op.create_unique_constraint('organization_api_key_hash_key', 'organization', ['api_key_hash'])


def downgrade() -> None:
    op.drop_constraint('organization_api_key_hash_key', 'organization', type_='unique')
    op.drop_column('organization', 'api_key_hint')
    op.drop_column('organization', 'api_key_hash')
