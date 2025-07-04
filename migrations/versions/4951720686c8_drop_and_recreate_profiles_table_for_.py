"""Drop and recreate profiles table for full reset

Revision ID: 4951720686c8
Revises: 39d040298944
Create Date: 2025-07-01 15:06:44.772464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4951720686c8'
down_revision = '39d040298944'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('profiles')
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('parent_name', sa.String(length=120), nullable=False),
        sa.Column('parent_phone', sa.String(length=20), nullable=False),
        sa.Column('student_phone', sa.String(length=20), nullable=False),
        sa.Column('student_class', sa.String(length=20), nullable=False),
        sa.Column('school_name', sa.String(length=120), nullable=False),
        sa.Column('roll_number', sa.Integer(), unique=True),
        sa.Column('last_seen_pdf_id', sa.Integer(), default=0),
        sa.Column('last_seen_test_id', sa.Integer(), default=0),
        sa.Column('last_seen_notification_id', sa.Integer(), default=0),
        sa.Column('last_seen_personal_notification_id', sa.Integer(), default=0),
        sa.Column('profile_pic', sa.String(length=256)),
        sa.Column('pending_popup', sa.Text()),
    )


def downgrade():
    op.drop_table('profiles')
