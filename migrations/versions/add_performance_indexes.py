"""Add performance indexes for PostgreSQL

Revision ID: add_performance_indexes
Revises: cf90f20ca95d
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'cf90f20ca95d'
branch_labels = None
depends_on = None

def upgrade():
    # Add indexes for better performance on PostgreSQL
    
    # Index for user authentication
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_is_admin', 'users', ['is_admin'])
    
    # Index for profile queries
    op.create_index('idx_profile_user_id', 'profiles', ['user_id'])
    op.create_index('idx_profile_student_class', 'profiles', ['student_class'])
    op.create_index('idx_profile_roll_number', 'profiles', ['roll_number'])
    
    # Index for fee management
    op.create_index('idx_fee_user_id', 'fees', ['user_id'])
    op.create_index('idx_fee_month', 'fees', ['month'])
    op.create_index('idx_fee_is_paid', 'fees', ['is_paid'])
    op.create_index('idx_fee_user_month', 'fees', ['user_id', 'month'])
    
    # Index for payments
    op.create_index('idx_payment_user_id', 'payments', ['user_id'])
    op.create_index('idx_payment_fee_id', 'payments', ['fee_id'])
    op.create_index('idx_payment_is_confirmed', 'payments', ['is_confirmed'])
    op.create_index('idx_payment_method', 'payments', ['method'])
    
    # Index for marks and tests
    op.create_index('idx_mark_user_id', 'marks', ['user_id'])
    op.create_index('idx_mark_test_id', 'marks', ['test_id'])
    op.create_index('idx_test_date', 'tests', ['date'])
    
    # Index for notifications
    op.create_index('idx_notification_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'])
    
    # Index for PDFs
    op.create_index('idx_pdf_uploaded_at', 'pdfs', ['uploaded_at'])
    
    # PostgreSQL-specific optimizations
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Partial indexes for better performance
        op.execute('CREATE INDEX idx_fee_unpaid ON fees (user_id, month) WHERE is_paid = false')
        op.execute('CREATE INDEX idx_payment_pending ON payments (user_id, requested_at) WHERE is_confirmed = false')
        # Text search indexes for better search performance
        op.execute("CREATE INDEX idx_profile_name_search ON profiles USING gin(to_tsvector('english', full_name))")
        op.execute("CREATE INDEX idx_pdf_title_search ON pdfs USING gin(to_tsvector('english', title))")

def downgrade():
    # Remove PostgreSQL-specific indexes first
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP INDEX IF EXISTS idx_fee_unpaid')
        op.execute('DROP INDEX IF EXISTS idx_payment_pending')
        op.execute('DROP INDEX IF EXISTS idx_profile_name_search')
        op.execute('DROP INDEX IF EXISTS idx_pdf_title_search')
    
    # Remove standard indexes
    op.drop_index('idx_user_email', 'users')
    op.drop_index('idx_user_is_admin', 'users')
    op.drop_index('idx_profile_user_id', 'profiles')
    op.drop_index('idx_profile_student_class', 'profiles')
    op.drop_index('idx_profile_roll_number', 'profiles')
    op.drop_index('idx_fee_user_id', 'fees')
    op.drop_index('idx_fee_month', 'fees')
    op.drop_index('idx_fee_is_paid', 'fees')
    op.drop_index('idx_fee_user_month', 'fees')
    op.drop_index('idx_payment_user_id', 'payments')
    op.drop_index('idx_payment_fee_id', 'payments')
    op.drop_index('idx_payment_is_confirmed', 'payments')
    op.drop_index('idx_payment_method', 'payments')
    op.drop_index('idx_mark_user_id', 'marks')
    op.drop_index('idx_mark_test_id', 'marks')
    op.drop_index('idx_test_date', 'tests')
    op.drop_index('idx_notification_user_id', 'notifications')
    op.drop_index('idx_notification_created_at', 'notifications')
    op.drop_index('idx_pdf_uploaded_at', 'pdfs') 