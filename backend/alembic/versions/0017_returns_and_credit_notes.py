from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0017'
down_revision: Union[str, None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('payment_refunds', sa.Column('status', sa.String(length=32), nullable=False, server_default='confirmed'))
    op.add_column('payment_refunds', sa.Column('provider_reference', sa.String(length=128), nullable=True))
    op.add_column('payment_refunds', sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'))
    op.add_column('payment_refunds', sa.Column('failure_reason', sa.Text(), nullable=True))
    op.add_column('payment_refunds', sa.Column('return_id', sa.Uuid(), nullable=True))
    op.add_column('payment_refunds', sa.Column('idempotency_key', sa.String(length=128), nullable=True))

    op.create_table(
        'credit_notes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', sa.Uuid(), nullable=True),
        sa.Column('customer_id', sa.Uuid(), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sale_id', sa.Uuid(), sa.ForeignKey('sales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('return_id', sa.Uuid(), nullable=True),
        sa.Column('series', sa.String(length=16), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('subtotal_amount', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('tax_amount', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('total_amount', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('reason_code', sa.String(length=32), nullable=False, server_default='02_DEVOLUCION'),
        sa.Column('reason_description', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='issued'),
        sa.Column('issued_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_notes_company_id'), 'credit_notes', ['company_id'], unique=False)
    op.create_index(op.f('ix_credit_notes_customer_id'), 'credit_notes', ['customer_id'], unique=False)
    op.create_index(op.f('ix_credit_notes_sale_id'), 'credit_notes', ['sale_id'], unique=False)

    op.create_table(
        'credit_note_lines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('credit_note_id', sa.Uuid(), sa.ForeignKey('credit_notes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sale_line_id', sa.Uuid(), nullable=True),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 6), nullable=False),
        sa.Column('unit_price', sa.Numeric(20, 6), nullable=False),
        sa.Column('discount_amount', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('tax_rate', sa.Numeric(6, 4), nullable=False, server_default='0.1800'),
        sa.Column('subtotal_amount', sa.Numeric(20, 6), nullable=False),
        sa.Column('tax_amount', sa.Numeric(20, 6), nullable=False),
        sa.Column('total_amount', sa.Numeric(20, 6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_note_lines_credit_note_id'), 'credit_note_lines', ['credit_note_id'], unique=False)

    op.create_table(
        'customer_credit_movements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('customer_id', sa.Uuid(), sa.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('movement_type', sa.String(length=32), nullable=False),
        sa.Column('amount_delta', sa.Numeric(20, 6), nullable=False),
        sa.Column('resulting_balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('reference_type', sa.String(length=32), nullable=False),
        sa.Column('reference_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_credit_movements_company_id'), 'customer_credit_movements', ['company_id'], unique=False)
    op.create_index(op.f('ix_customer_credit_movements_customer_id'), 'customer_credit_movements', ['customer_id'], unique=False)


def downgrade() -> None:
    op.drop_table('customer_credit_movements')
    op.drop_table('credit_note_lines')
    op.drop_table('credit_notes')
    op.drop_column('payment_refunds', 'idempotency_key')
    op.drop_column('payment_refunds', 'return_id')
    op.drop_column('payment_refunds', 'failure_reason')
    op.drop_column('payment_refunds', 'currency')
    op.drop_column('payment_refunds', 'provider_reference')
    op.drop_column('payment_refunds', 'status')
