from alembic import op
import sqlalchemy as sa

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("supplier_products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id"), nullable=False, index=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("purchase_presentation", sa.String(128), nullable=False),
        sa.Column("supplier_sku", sa.String(128), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(20, 6), nullable=False),
        sa.Column("minimum_quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("order_multiple", sa.Numeric(20, 6), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "supplier_id", "product_id", "currency", name="uq_supplier_product_currency"),
        sa.CheckConstraint("unit_cost >= 0 AND minimum_quantity > 0 AND order_multiple > 0 AND lead_time_days >= 0", name="ck_supplier_product_values"),
        sa.CheckConstraint("valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from", name="ck_supplier_product_dates"))
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "supplier_products" ENABLE ROW LEVEL SECURITY')
        op.execute('ALTER TABLE "supplier_products" FORCE ROW LEVEL SECURITY')
        op.execute("CREATE POLICY tenant_scope ON supplier_products USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("El catálogo y sus condiciones de compra deben conservarse.")
