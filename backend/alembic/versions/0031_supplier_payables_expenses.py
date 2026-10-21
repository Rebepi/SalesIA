from alembic import op
import sqlalchemy as sa

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def identifiers():
    return [sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True)]


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.create_table("supplier_payables", *identifiers(),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=False, index=True),
        sa.Column("purchase_order_id", sa.Uuid(), sa.ForeignKey("supply_documents.id")),
        sa.Column("document_number", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("paid_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False), *timestamps(),
        sa.UniqueConstraint("company_id", "supplier_id", "document_number", name="uq_payable_supplier_document"),
        sa.CheckConstraint("amount > 0 AND paid_amount >= 0 AND paid_amount <= amount", name="payable_balances"))
    op.create_table("supplier_payable_installments", *identifiers(),
        sa.Column("payable_id", sa.Uuid(), sa.ForeignKey("supplier_payables.id"), nullable=False, index=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("paid_amount", sa.Numeric(20, 6), nullable=False),
        sa.UniqueConstraint("payable_id", "sequence", name="uq_payable_installment_sequence"),
        sa.CheckConstraint("amount > 0 AND paid_amount >= 0 AND paid_amount <= amount", name="payable_installment_balances"))
    op.create_table("supplier_payable_payments", *identifiers(),
        sa.Column("payable_id", sa.Uuid(), sa.ForeignKey("supplier_payables.id"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("allocations_json", sa.Text(), nullable=False),
        sa.Column("reversal_reason", sa.Text()),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False), *timestamps(),
        sa.CheckConstraint("amount > 0", name="payable_payment_positive"))
    op.create_table("cost_centers", *identifiers(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), *timestamps(),
        sa.UniqueConstraint("company_id", "code", name="uq_cost_center_code"))
    op.create_table("operating_expenses", *identifiers(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("document_number", sa.String(128)),
        sa.Column("expense_date", sa.Date(), nullable=False, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("notes", sa.Text(), nullable=False), *timestamps(),
        sa.CheckConstraint("amount > 0", name="expense_positive"))
    op.create_table("expense_allocations", *identifiers(),
        sa.Column("expense_id", sa.Uuid(), sa.ForeignKey("operating_expenses.id"), nullable=False, index=True),
        sa.Column("cost_center_id", sa.Uuid(), sa.ForeignKey("cost_centers.id"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.UniqueConstraint("expense_id", "cost_center_id", name="uq_expense_center"),
        sa.CheckConstraint("amount > 0", name="expense_allocation_positive"))
    op.create_table("cost_budgets", *identifiers(),
        sa.Column("cost_center_id", sa.Uuid(), sa.ForeignKey("cost_centers.id"), nullable=False, index=True),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), *timestamps(),
        sa.UniqueConstraint("company_id", "cost_center_id", "period", "currency", name="uq_cost_budget_period"),
        sa.CheckConstraint("amount >= 0", name="cost_budget_nonnegative"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("supplier_payables", "supplier_payable_installments", "supplier_payable_payments", "cost_centers", "operating_expenses", "expense_allocations", "cost_budgets"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Las obligaciones y movimientos financieros deben conservarse. Restaura un respaldo para revertir.")
