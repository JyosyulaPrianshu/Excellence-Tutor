"""Add class_for column to notifications table

Revision ID: add_class_for_to_notifications
Revises: add_class_for_to_resources_pdfs_tests
Create Date: 2024-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_class_for_to_notifications'
down_revision = 'add_class_for_to_resources_pdfs_tests'

def upgrade():
    op.add_column('notifications', sa.Column('class_for', sa.String(length=20), nullable=True))

def downgrade():
    op.drop_column('notifications', 'class_for') 