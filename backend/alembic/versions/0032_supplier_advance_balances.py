from alembic import op
import sqlalchemy as sa

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("supplier_balance_movements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=False, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount_delta", sa.Numeric(20, 6), nullable=False),
        sa.Column("movement_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("reference", sa.String(128), nullable=False),
        sa.Column("payment_id", sa.Uuid(), sa.ForeignKey("supplier_payable_payments.id")),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE supplier_balance_movements ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE supplier_balance_movements FORCE ROW LEVEL SECURITY")
        op.execute("CREATE POLICY tenant_scope ON supplier_balance_movements USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Los anticipos y créditos deben conservarse.")
