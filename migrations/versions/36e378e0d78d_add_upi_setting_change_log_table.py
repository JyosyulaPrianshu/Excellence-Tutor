"""Add UPISettingChangeLog table

Revision ID: 36e378e0d78d
Revises: ae4394dbfc65
Create Date: 2025-07-04 08:22:21.480454

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '36e378e0d78d'
down_revision = 'ae4394dbfc65'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('upi_setting_change_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('admin_user_id', sa.Integer(), nullable=True),
    sa.Column('field_changed', sa.String(length=32), nullable=False),
    sa.Column('old_value', sa.String(length=256), nullable=True),
    sa.Column('new_value', sa.String(length=256), nullable=True),
    sa.Column('changed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('fees', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('idx_fee_unpaid'), postgresql_where='(is_paid = false)')

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('idx_payment_pending'), postgresql_where='(is_confirmed = false)')

    with op.batch_alter_table('pdfs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('idx_pdf_title_search'), postgresql_using='gin')

    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('profiles_roll_number_key'), type_='unique')
        batch_op.create_unique_constraint('unique_roll_per_class', ['student_class', 'roll_number'])

    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_constraint('unique_roll_per_class', type_='unique')
        batch_op.create_unique_constraint(batch_op.f('profiles_roll_number_key'), ['roll_number'], postgresql_nulls_not_distinct=False)

    with op.batch_alter_table('pdfs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_pdf_title_search'), [sa.literal_column("to_tsvector('english'::regconfig, title::text)")], unique=False, postgresql_using='gin')

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_payment_pending'), ['user_id', 'requested_at'], unique=False, postgresql_where='(is_confirmed = false)')

    with op.batch_alter_table('fees', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('idx_fee_unpaid'), ['user_id', 'month'], unique=False, postgresql_where='(is_paid = false)')

    op.drop_table('upi_setting_change_logs')
    # ### end Alembic commands ### 