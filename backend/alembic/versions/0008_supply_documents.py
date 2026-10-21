from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_stocks", sa.Column("average_cost", sa.Numeric(20, 6), nullable=False, server_default="0"))
    op.create_table("suppliers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("tax_id", sa.String(32), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(64)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("company_id", "tax_id"))
    op.create_index("ix_suppliers_company_id", "suppliers", ["company_id"])
    op.create_table("supply_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Uuid(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("source_warehouse_id", sa.Uuid(), sa.ForeignKey("warehouses.id")),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id")),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id")),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("supply_documents.id")),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "id"))
    for column in ("company_id", "kind", "sale_id", "parent_id"):
        op.create_index(f"ix_supply_documents_{column}", "supply_documents", [column])
    op.create_table("supply_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("processed_quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit_cost", sa.Numeric(20, 6), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "document_id"], ["supply_documents.company_id", "supply_documents.id"]),
        sa.ForeignKeyConstraint(["company_id", "product_id"], ["products.company_id", "products.id"]),
        sa.UniqueConstraint("document_id", "product_id"))
    for column in ("company_id", "document_id", "product_id"):
        op.create_index(f"ix_supply_lines_{column}", "supply_lines", [column])
    if op.get_bind().dialect.name == "postgresql":
        for table in ("suppliers", "supply_documents", "supply_lines"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    op.drop_table("supply_lines")
    op.drop_table("supply_documents")
    op.drop_table("suppliers")
    with op.batch_alter_table("inventory_stocks") as batch:
        batch.drop_column("average_cost")
