from alembic import op
import sqlalchemy as sa

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("payment_refunds") as batch:
        batch.add_column(sa.Column("unapplied_only", sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table("customer_credit_movements") as batch:
        batch.add_column(sa.Column("currency", sa.String(3), nullable=True))
        batch.add_column(sa.Column("payment_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_customer_credit_payment", "payments", ["payment_id"], ["id"])
        batch.create_index("ix_customer_credit_movements_currency", ["currency"])
        batch.create_index("ix_customer_credit_movements_payment_id", ["payment_id"])
    bind = op.get_bind()
    tables = ("customer_credit_movements", "credit_notes", "sales", "sales_returns")
    security = []
    if bind.dialect.name == "postgresql":
        for table in tables:
            flags = bind.execute(sa.text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = to_regclass(:table)"), {"table": table}).one()
            security.append((table, flags[0], flags[1]))
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("UPDATE customer_credit_movements SET currency = (SELECT currency FROM credit_notes WHERE credit_notes.id = customer_credit_movements.reference_id AND credit_notes.company_id = customer_credit_movements.company_id) WHERE reference_type = 'CREDIT_NOTE'")
    op.execute("UPDATE customer_credit_movements SET currency = (SELECT currency FROM sales WHERE sales.id = customer_credit_movements.reference_id AND sales.company_id = customer_credit_movements.company_id) WHERE reference_type IN ('SALE', 'EXCHANGE_DIFF')")
    op.execute("UPDATE customer_credit_movements SET currency = (SELECT sales.currency FROM sales_returns JOIN sales ON sales.id = sales_returns.sale_id AND sales.company_id = sales_returns.company_id WHERE sales_returns.id = customer_credit_movements.reference_id AND sales_returns.company_id = customer_credit_movements.company_id) WHERE reference_type = 'RETURN'")
    for table, enabled, forced in security:
        if enabled:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        if forced:
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.create_table("customer_credit_allocations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("debit_id", sa.Uuid(), sa.ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("credit_id", sa.Uuid(), sa.ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("debit_id", "credit_id", name="uq_customer_credit_allocation_pair"),
        sa.CheckConstraint("amount > 0", name="customer_credit_allocation_amount"))
    op.create_table("customer_credit_reservations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("payment_id", sa.Uuid(), sa.ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="customer_credit_reservation_amount"))
    op.create_table("customer_credit_conversions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("source_currency", sa.String(3), nullable=False),
        sa.Column("target_currency", sa.String(3), nullable=False),
        sa.Column("source_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("target_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("rate", sa.Numeric(20, 10), nullable=False),
        sa.Column("rate_reference", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_ids_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("debit_id", sa.Uuid(), sa.ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("credit_id", sa.Uuid(), sa.ForeignKey("customer_credit_movements.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("source_amount > 0 AND target_amount > 0 AND rate > 0", name="customer_credit_conversion_amounts"),
        sa.CheckConstraint("source_currency <> target_currency", name="customer_credit_conversion_currencies"))
    if bind.dialect.name == "postgresql":
        for table in ("customer_credit_allocations", "customer_credit_reservations", "customer_credit_conversions"):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Se debe conservar la moneda y la procedencia de los créditos de clientes.")
