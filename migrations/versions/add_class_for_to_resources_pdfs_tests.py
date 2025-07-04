"""Add class_for column to resources, pdfs, and tests tables

Revision ID: add_class_for_to_resources_pdfs_tests
Revises: e149e87de828
Create Date: 2024-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_class_for_to_resources_pdfs_tests'
down_revision = 'e149e87de828'

def upgrade():
    op.add_column('resources', sa.Column('class_for', sa.String(length=20), nullable=False, server_default='all'))
    op.add_column('pdfs', sa.Column('class_for', sa.String(length=20), nullable=False, server_default='all'))
    op.add_column('tests', sa.Column('class_for', sa.String(length=20), nullable=False, server_default='all'))

def downgrade():
    op.drop_column('resources', 'class_for')
    op.drop_column('pdfs', 'class_for')
    op.drop_column('tests', 'class_for') 