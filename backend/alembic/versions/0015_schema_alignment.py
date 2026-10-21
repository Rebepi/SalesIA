from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0015'
down_revision: Union[str, None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_audit_logs_company_id'), 'audit_logs', ['company_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.drop_constraint('uq_companies_tax_id', 'companies', type_='unique')
    op.drop_index('ix_companies_tax_id', table_name='companies')
    op.create_index(op.f('ix_companies_tax_id'), 'companies', ['tax_id'], unique=True)
    op.create_index(op.f('ix_inventory_stocks_product_id'), 'inventory_stocks', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_stocks_warehouse_id'), 'inventory_stocks', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_kardex_movements_company_id'), 'kardex_movements', ['company_id'], unique=False)
    op.create_index(op.f('ix_kardex_movements_product_id'), 'kardex_movements', ['product_id'], unique=False)
    op.create_index(op.f('ix_kardex_movements_warehouse_id'), 'kardex_movements', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_outbox_events_company_id'), 'outbox_events', ['company_id'], unique=False)
    op.create_index(op.f('ix_payments_company_id'), 'payments', ['company_id'], unique=False)
    op.create_index(op.f('ix_payments_sale_id'), 'payments', ['sale_id'], unique=False)
    op.drop_constraint('uq_revoked_tokens_token_jti', 'revoked_tokens', type_='unique')
    op.drop_index('ix_revoked_tokens_token_jti', table_name='revoked_tokens')
    op.create_index(op.f('ix_revoked_tokens_token_jti'), 'revoked_tokens', ['token_jti'], unique=True)
    op.create_index(op.f('ix_sale_lines_product_id'), 'sale_lines', ['product_id'], unique=False)
    op.create_index(op.f('ix_sales_branch_id'), 'sales', ['branch_id'], unique=False)
    op.create_index(op.f('ix_sales_customer_id'), 'sales', ['customer_id'], unique=False)
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_index('ix_users_email', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_warehouses_branch_id'), 'warehouses', ['branch_id'], unique=False)
    op.create_table(
        'support_grants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('granted_by', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=64), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_support_grants_token_hash')
    )
    op.create_index(op.f('ix_support_grants_company_id'), 'support_grants', ['company_id'], unique=False)
    op.create_index(op.f('ix_support_grants_granted_by'), 'support_grants', ['granted_by'], unique=False)
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "support_grants" ENABLE ROW LEVEL SECURITY')
        op.execute('ALTER TABLE "support_grants" FORCE ROW LEVEL SECURITY')
        op.execute("CREATE POLICY support_grants_tenant_policy ON \"support_grants\" USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute('DROP POLICY IF EXISTS support_grants_tenant_policy ON "support_grants"')
    op.drop_index(op.f('ix_support_grants_granted_by'), table_name='support_grants')
    op.drop_index(op.f('ix_support_grants_company_id'), table_name='support_grants')
    op.drop_table('support_grants')
    op.drop_index(op.f('ix_warehouses_branch_id'), table_name='warehouses')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.drop_index(op.f('ix_sales_customer_id'), table_name='sales')
    op.drop_index(op.f('ix_sales_branch_id'), table_name='sales')
    op.drop_index(op.f('ix_sale_lines_product_id'), table_name='sale_lines')
    op.drop_index(op.f('ix_revoked_tokens_token_jti'), table_name='revoked_tokens')
    op.create_index('ix_revoked_tokens_token_jti', 'revoked_tokens', ['token_jti'], unique=False)
    op.create_unique_constraint('uq_revoked_tokens_token_jti', 'revoked_tokens', ['token_jti'])
    op.drop_index(op.f('ix_payments_sale_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_company_id'), table_name='payments')
    op.drop_index(op.f('ix_outbox_events_company_id'), table_name='outbox_events')
    op.drop_index(op.f('ix_kardex_movements_warehouse_id'), table_name='kardex_movements')
    op.drop_index(op.f('ix_kardex_movements_product_id'), table_name='kardex_movements')
    op.drop_index(op.f('ix_kardex_movements_company_id'), table_name='kardex_movements')
    op.drop_index(op.f('ix_inventory_stocks_warehouse_id'), table_name='inventory_stocks')
    op.drop_index(op.f('ix_inventory_stocks_product_id'), table_name='inventory_stocks')
    op.drop_index(op.f('ix_companies_tax_id'), table_name='companies')
    op.create_index('ix_companies_tax_id', 'companies', ['tax_id'], unique=False)
    op.create_unique_constraint('uq_companies_tax_id', 'companies', ['tax_id'])
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_company_id'), table_name='audit_logs')
