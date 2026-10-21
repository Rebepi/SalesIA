from alembic import op
import sqlalchemy as sa

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "landed_cost_adjustments" not in tables:
        op.create_table("landed_cost_adjustments",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
            sa.Column("goods_receipt_id", sa.Uuid(), sa.ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("charge_type", sa.String(64), nullable=False),
            sa.Column("amount", sa.Numeric(20, 6), nullable=False),
            sa.Column("allocation_method", sa.String(32), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if "purchase_invoice_matches" not in tables:
        op.create_table("purchase_invoice_matches",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
            sa.Column("purchase_order_id", sa.Uuid(), sa.ForeignKey("supply_documents.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("goods_receipt_id", sa.Uuid(), sa.ForeignKey("supply_documents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("invoice_number", sa.String(64), nullable=False),
            sa.Column("invoice_amount", sa.Numeric(20, 6), nullable=False),
            sa.Column("matched_amount", sa.Numeric(20, 6), nullable=False),
            sa.Column("discrepancy_amount", sa.Numeric(20, 6), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("landed_cost_adjustments", "purchase_invoice_matches"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f'DROP POLICY IF EXISTS tenant_scope ON "{table}"')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("La migración conserva las conciliaciones y los costos registrados. Restaura un respaldo para revertir el esquema.")
