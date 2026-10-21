from alembic import op
import sqlalchemy as sa

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("return_settlement_movements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("return_id", sa.Uuid(), sa.ForeignKey("sales_returns.id"), nullable=False, index=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("reference_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "kind", "reference_id", name="uq_return_settlement_reference"),
        sa.CheckConstraint("amount > 0", name="ck_return_settlement_amount"))
    with op.batch_alter_table("payment_refunds") as batch:
        batch.add_column(sa.Column("cash_session_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_refund_cash_session", "cash_sessions", ["cash_session_id"], ["id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE return_settlement_movements ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE return_settlement_movements FORCE ROW LEVEL SECURITY")
        op.execute("CREATE POLICY tenant_scope ON return_settlement_movements USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Las aplicaciones de devoluciones y su custodia monetaria deben conservarse.")
