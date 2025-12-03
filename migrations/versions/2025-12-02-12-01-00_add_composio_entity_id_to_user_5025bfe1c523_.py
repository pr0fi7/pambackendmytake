"""add_composio_entity_id_to_user

Revision ID: 5025bfe1c523
Revises: 6baf7e83555b
Create Date: 2025-12-02 12:01:00.819749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5025bfe1c523'
down_revision: Union[str, Sequence[str], None] = '6baf7e83555b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composio_entity_id column to users table."""
    op.add_column('users', sa.Column('composio_entity_id', sa.String(), nullable=True), schema='pam')


def downgrade() -> None:
    """Remove composio_entity_id column from users table."""
    op.drop_column('users', 'composio_entity_id', schema='pam')
