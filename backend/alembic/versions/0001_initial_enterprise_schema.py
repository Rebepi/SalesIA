from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tax_id", sa.String(length=32), nullable=False, unique=True),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("trade_name", sa.String(length=255), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_companies_tax_id", "companies", ["tax_id"])

    op.create_table(
        "branches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_branches_company_code"),
        sa.UniqueConstraint("company_id", "id", name="uq_branches_company_id"),
    )
    op.create_index("ix_branches_company_id", "branches", ["company_id"])

    op.create_table(
        "warehouses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "branch_id"], ["branches.company_id", "branches.id"], name="fk_warehouses_branch_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "code", name="uq_warehouses_company_code"),
        sa.UniqueConstraint("company_id", "id", name="uq_warehouses_company_id"),
    )
    op.create_index("ix_warehouses_company_id", "warehouses", ["company_id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("doc_type", sa.String(length=16), nullable=False),
        sa.Column("doc_number", sa.String(length=32), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("credit_limit", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("current_balance", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "doc_type", "doc_number", name="uq_customers_doc"),
        sa.UniqueConstraint("company_id", "id", name="uq_customers_company_id"),
        sa.CheckConstraint("credit_limit >= 0", name="ck_customers_credit_limit_positive"),
        sa.CheckConstraint("current_balance >= 0", name="ck_customers_current_balance_positive"),
    )
    op.create_index("ix_customers_company_id", "customers", ["company_id"])

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=16), nullable=False, server_default="NIU"),
        sa.Column("unit_cost", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("unit_price", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("tax_rate", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0.1800"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "sku", name="uq_products_company_sku"),
        sa.UniqueConstraint("company_id", "id", name="uq_products_company_id"),
        sa.CheckConstraint("unit_price >= 0", name="ck_products_unit_price_non_negative"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_products_unit_cost_non_negative"),
        sa.CheckConstraint("tax_rate >= 0", name="ck_products_tax_rate_non_negative"),
    )
    op.create_index("ix_products_company_id", "products", ["company_id"])

    op.create_table(
        "inventory_stocks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("physical_quantity", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("reserved_quantity", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "warehouse_id"], ["warehouses.company_id", "warehouses.id"], name="fk_inventory_warehouse_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["company_id", "product_id"], ["products.company_id", "products.id"], name="fk_inventory_product_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "warehouse_id", "product_id", name="uq_inventory_warehouse_product"),
        sa.CheckConstraint("physical_quantity >= 0", name="ck_stock_physical_non_negative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_stock_reserved_non_negative"),
        sa.CheckConstraint("physical_quantity >= reserved_quantity", name="ck_stock_physical_gte_reserved"),
    )
    op.create_index("ix_inventory_stocks_company_id", "inventory_stocks", ["company_id"])

    op.create_table(
        "sales",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("series", sa.String(length=16), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("subtotal_amount", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("tax_amount", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("total_amount", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("paid_amount", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id", "branch_id"], ["branches.company_id", "branches.id"], name="fk_sales_branch_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["company_id", "customer_id"], ["customers.company_id", "customers.id"], name="fk_sales_customer_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "id", name="uq_sales_company_id"),
        sa.UniqueConstraint("company_id", "series", "number", name="uq_sales_series_number"),
        sa.CheckConstraint("status IN ('draft', 'confirmed', 'paid', 'cancelled', 'refunded')", name="ck_sales_valid_status"),
        sa.CheckConstraint("subtotal_amount >= 0", name="ck_sales_subtotal_positive"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_sales_tax_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_sales_total_positive"),
        sa.CheckConstraint("paid_amount >= 0", name="ck_sales_paid_positive"),
    )
    op.create_index("ix_sales_company_id", "sales", ["company_id"])
    op.create_index("ix_sales_company_status_created", "sales", ["company_id", "status", "created_at"])

    op.create_table(
        "sale_lines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sale_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("sku_snapshot", sa.String(length=64), nullable=False),
        sa.Column("name_snapshot", sa.String(length=255), nullable=False),
        sa.Column("unit_of_measure_snapshot", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit_price_snapshot", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit_cost_snapshot", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=20, scale=6), nullable=False, server_default="0.000000"),
        sa.Column("tax_rate_snapshot", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("tax_amount", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "sale_id"], ["sales.company_id", "sales.id"], name="fk_sale_lines_sale_scope", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id", "product_id"], ["products.company_id", "products.id"], name="fk_sale_lines_product_scope", ondelete="RESTRICT"),
        sa.UniqueConstraint("sale_id", "line_number", name="uq_sale_lines_line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_sale_lines_qty_strictly_positive"),
        sa.CheckConstraint("unit_price_snapshot >= 0", name="ck_sale_lines_price_positive"),
        sa.CheckConstraint("unit_cost_snapshot >= 0", name="ck_sale_lines_cost_positive"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_sale_lines_discount_positive"),
        sa.CheckConstraint("tax_rate_snapshot >= 0", name="ck_sale_lines_tax_rate_positive"),
        sa.CheckConstraint("subtotal_amount >= 0", name="ck_sale_lines_subtotal_positive"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_sale_lines_tax_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_sale_lines_total_positive"),
    )
    op.create_index("ix_sale_lines_company_id", "sale_lines", ["company_id"])
    op.create_index("ix_sale_lines_sale_id", "sale_lines", ["sale_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sale_id", sa.Uuid(), nullable=False),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("reference_code", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "sale_id"], ["sales.company_id", "sales.id"], name="fk_payments_sale_scope", ondelete="RESTRICT"),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_strictly_positive"),
        sa.CheckConstraint("status IN ('pending', 'confirmed', 'failed', 'refunded')", name="ck_payments_valid_status"),
    )
    op.create_index("ix_payments_company_sale", "payments", ["company_id", "sale_id"])

    op.create_table(
        "kardex_movements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("warehouse_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("movement_type", sa.String(length=32), nullable=False),
        sa.Column("reference_doc_type", sa.String(length=32), nullable=False),
        sa.Column("reference_doc_id", sa.Uuid(), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("resulting_physical_qty", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("moving_average_cost", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id", "warehouse_id"], ["warehouses.company_id", "warehouses.id"], name="fk_kardex_warehouse_scope", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["company_id", "product_id"], ["products.company_id", "products.id"], name="fk_kardex_product_scope", ondelete="RESTRICT"),
        sa.CheckConstraint("resulting_physical_qty >= 0", name="ck_kardex_resulting_qty_positive"),
    )
    op.create_index("ix_kardex_company_product_occurred", "kardex_movements", ["company_id", "product_id", "occurred_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("payload_diff", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_company_entity", "audit_logs", ["company_id", "entity_type", "entity_id"])
    op.create_index("ix_audit_logs_trace_id", "audit_logs", ["trace_id"])

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_status_created", "outbox_events", ["status", "created_at"])
    op.create_index("ix_outbox_events_company_status", "outbox_events", ["company_id", "status"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("audit_logs")
    op.drop_table("kardex_movements")
    op.drop_table("payments")
    op.drop_table("sale_lines")
    op.drop_table("sales")
    op.drop_table("inventory_stocks")
    op.drop_table("products")
    op.drop_table("customers")
    op.drop_table("warehouses")
    op.drop_table("branches")
    op.drop_table("companies")
