"""Add seen column to notifications table

Revision ID: add_seen_to_notifications
Revises: add_class_for_to_notifications
Create Date: 2024-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_seen_to_notifications'
down_revision = 'add_class_for_to_notifications'

def upgrade():
    op.add_column('notifications', sa.Column('seen', sa.Boolean(), nullable=False, server_default=sa.text('0')))

def downgrade():
    op.drop_column('notifications', 'seen') 