from alembic import op
import sqlalchemy as sa

revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("supplier_claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=False, index=True),
        sa.Column("purchase_order_id", sa.Uuid(), sa.ForeignKey("supply_documents.id"), nullable=False, index=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("reason_type", sa.String(32), nullable=False),
        sa.Column("resolution", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("expected_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("agreed_amount", sa.Numeric(20, 6), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("items_json", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("acknowledged_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_supplier_claim_code"),
        sa.CheckConstraint("expected_amount >= 0 AND (agreed_amount IS NULL OR agreed_amount >= 0)", name="ck_supplier_claim_amounts"))
    op.add_column("supply_documents", sa.Column("supplier_claim_id", sa.Uuid(), nullable=True, index=True))
    with op.batch_alter_table("supply_documents") as batch:
        batch.create_foreign_key("fk_supply_supplier_claim", "supplier_claims", ["supplier_claim_id"], ["id"], ondelete="RESTRICT")
    op.add_column("supplier_balance_movements", sa.Column("source_claim_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("supplier_balance_movements", sa.Column("source_document_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("supplier_balance_movements", sa.Column("reversal_of_id", sa.Uuid(), nullable=True))
    op.add_column("supplier_balance_movements", sa.Column("allocations_json", sa.Text(), nullable=False, server_default="[]"))
    with op.batch_alter_table("supplier_balance_movements") as batch:
        batch.create_foreign_key("fk_supplier_balance_claim", "supplier_claims", ["source_claim_id"], ["id"], ondelete="RESTRICT")
        batch.create_foreign_key("fk_supplier_balance_source_document", "supply_documents", ["source_document_id"], ["id"], ondelete="RESTRICT")
        batch.create_foreign_key("fk_supplier_balance_reversal", "supplier_balance_movements", ["reversal_of_id"], ["id"], ondelete="RESTRICT")
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "supplier_claims" ENABLE ROW LEVEL SECURITY')
        op.execute('ALTER TABLE "supplier_claims" FORCE ROW LEVEL SECURITY')
        op.execute("CREATE POLICY tenant_scope ON supplier_claims USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Los reclamos, créditos y sus aplicaciones deben conservarse.")
