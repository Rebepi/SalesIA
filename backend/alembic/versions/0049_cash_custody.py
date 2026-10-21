from alembic import op
import sqlalchemy as sa

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade():
    security = None
    if op.get_bind().dialect.name == "postgresql":
        security = op.get_bind().execute(sa.text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'cash_sessions'::regclass")).first()
        if security and security[0]:
            op.execute("ALTER TABLE cash_sessions DISABLE ROW LEVEL SECURITY")
    op.add_column("cash_sessions", sa.Column("currency", sa.String(3), nullable=True))
    op.execute("UPDATE cash_sessions SET currency = (SELECT companies.base_currency FROM companies WHERE companies.id = cash_sessions.company_id) WHERE currency IS NULL")
    with op.batch_alter_table("cash_sessions") as batch:
        batch.alter_column("currency", existing_type=sa.String(3), nullable=False)
    if security and security[0]:
        op.execute("ALTER TABLE cash_sessions ENABLE ROW LEVEL SECURITY")
        if security[1]:
            op.execute("ALTER TABLE cash_sessions FORCE ROW LEVEL SECURITY")
    op.create_table("cash_custody_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("branch_id", sa.Uuid(), sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("responsible_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("balance", sa.Numeric(20, 6), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("movements_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_cash_custody_account_code"),
        sa.CheckConstraint("balance >= 0", name="ck_cash_custody_account_balance"))
    op.create_table("cash_custody_transfers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("source_session_id", sa.Uuid(), sa.ForeignKey("cash_sessions.id"), nullable=True, index=True),
        sa.Column("source_account_id", sa.Uuid(), sa.ForeignKey("cash_custody_accounts.id"), nullable=True, index=True),
        sa.Column("destination_session_id", sa.Uuid(), sa.ForeignKey("cash_sessions.id"), nullable=True, index=True),
        sa.Column("destination_account_id", sa.Uuid(), sa.ForeignKey("cash_custody_accounts.id"), nullable=True, index=True),
        sa.Column("sender_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("receiver_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_cash_custody_transfer_code"),
        sa.CheckConstraint("amount > 0", name="ck_cash_custody_transfer_amount"),
        sa.CheckConstraint("(source_session_id IS NOT NULL AND source_account_id IS NULL) OR (source_session_id IS NULL AND source_account_id IS NOT NULL)", name="ck_cash_custody_source"),
        sa.CheckConstraint("(destination_session_id IS NOT NULL AND destination_account_id IS NULL) OR (destination_session_id IS NULL AND destination_account_id IS NOT NULL)", name="ck_cash_custody_destination"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("cash_custody_accounts", "cash_custody_transfers"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("La custodia y sus movimientos de efectivo deben conservarse.")
