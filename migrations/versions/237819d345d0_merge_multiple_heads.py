"""Merge multiple heads

Revision ID: 237819d345d0
Revises: 44a57895a877, add_performance_indexes
Create Date: 2025-06-29 13:44:43.604553

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '237819d345d0'
down_revision = ('44a57895a877', 'add_performance_indexes')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
