"""add_integrations_and_user_integrations_tables

Revision ID: 6baf7e83555b
Revises: fa0d7fc468ec
Create Date: 2025-11-27 09:45:40.756127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6baf7e83555b'
down_revision: Union[str, Sequence[str], None] = 'fa0d7fc468ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('image', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        schema='pam'
    )
    op.create_index('ix_pam_integrations_slug', 'integrations', ['slug'], unique=False, schema='pam')

    # Create user_integrations table
    op.create_table(
        'user_integrations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('composio_connection_id', sa.String(length=255), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['pam.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integration_id'], ['pam.integrations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='pam'
    )
    op.create_index('ix_pam_user_integrations_user_id', 'user_integrations', ['user_id'], unique=False, schema='pam')
    op.create_index('ix_pam_user_integrations_integration_id', 'user_integrations', ['integration_id'], unique=False, schema='pam')
    op.create_index('ix_pam_user_integrations_status', 'user_integrations', ['status'], unique=False, schema='pam')

    # Seed integrations data
    op.execute("""
        INSERT INTO pam.integrations (name, slug, image) VALUES
        ('Google Gmail', 'gmail', 'gmail.png'),
        ('Slack', 'slack', 'slack.png'),
        ('Notion', 'notion', 'notion.png'),
        ('HubSpot', 'hubspot', 'hubspot.png'),
        ('Google Calendar', 'googlecalendar', 'google-calendar.png'),
        ('Trello', 'trello', 'trello.png')
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_pam_user_integrations_status', table_name='user_integrations', schema='pam')
    op.drop_index('ix_pam_user_integrations_integration_id', table_name='user_integrations', schema='pam')
    op.drop_index('ix_pam_user_integrations_user_id', table_name='user_integrations', schema='pam')
    op.drop_table('user_integrations', schema='pam')
    op.drop_index('ix_pam_integrations_slug', table_name='integrations', schema='pam')
    op.drop_table('integrations', schema='pam')
