from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

TABLES = ("branches", "warehouses", "customers", "products", "inventory_stocks", "sales", "sale_lines", "payments", "kardex_movements", "audit_logs", "outbox_events", "jobs", "attachments", "backup_snapshots", "quotations", "orders", "cash_sessions", "custom_roles", "idempotency_records", "document_sequences", "payment_refunds", "company_settings")


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'CREATE POLICY tenant_scope ON "{table}" USING (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid) WITH CHECK (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid)')


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return
    for table in TABLES:
        op.execute(f'DROP POLICY tenant_scope ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
