from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def timestamp_columns():
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("categories"):
        op.create_table(
            "categories",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
            sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "code", name="uq_categories_company_code")
        )
        op.create_index("ix_categories_company_id", "categories", ["company_id"])
        op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("product_profiles"):
        op.create_table(
            "product_profiles",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("product_type", sa.String(32), nullable=False, server_default="product"),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("track_inventory", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
            sa.Column("barcode", sa.String(64), nullable=True),
            sa.Column("warranty_period_months", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("warranty_policy", sa.String(255), nullable=True),
            sa.Column("is_kit", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("price_includes_tax", sa.Boolean(), nullable=False, server_default=sa.false()),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "product_id", name="uq_product_profiles_product")
        )
        op.create_index("ix_product_profiles_company_id", "product_profiles", ["company_id"])
        op.create_index("ix_product_profiles_product_id", "product_profiles", ["product_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("product_variants"):
        op.create_table(
            "product_variants",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("sku", sa.String(64), nullable=False),
            sa.Column("attributes_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("price_delta", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "sku", name="uq_product_variants_sku")
        )
        op.create_index("ix_product_variants_company_id", "product_variants", ["company_id"])
        op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("product_barcodes"):
        op.create_table(
            "product_barcodes",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
            sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True),
            sa.Column("barcode", sa.String(64), nullable=False),
            sa.Column("barcode_type", sa.String(32), nullable=False, server_default="EAN13"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "barcode", name="uq_product_barcodes_company_code")
        )
        op.create_index("ix_product_barcodes_company_id", "product_barcodes", ["company_id"])
        op.create_index("ix_product_barcodes_product_id", "product_barcodes", ["product_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("units_of_measure"):
        op.create_table(
            "units_of_measure",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("code", sa.String(16), nullable=False),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("allow_fractions", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("precision_digits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "code", name="uq_units_of_measure_company_code")
        )
        op.create_index("ix_units_of_measure_company_id", "units_of_measure", ["company_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("customer_profiles"):
        op.create_table(
            "customer_profiles",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("assigned_sales_rep_id", sa.Uuid(), nullable=True),
            sa.Column("sales_team", sa.String(128), nullable=True),
            sa.Column("backup_sales_rep_id", sa.Uuid(), nullable=True),
            sa.Column("price_list_id", sa.String(64), nullable=True),
            sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
            sa.Column("preferred_currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("is_credit_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("credit_block_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("credit_block_reason", sa.String(255), nullable=True),
            sa.Column("tags_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("assignment_history_json", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "customer_id", name="uq_customer_profile_scope")
        )
        op.create_index("ix_customer_profiles_company_id", "customer_profiles", ["company_id"])
        op.create_index("ix_customer_profiles_customer_id", "customer_profiles", ["customer_id"])
        op.create_index("ix_customer_profiles_assigned_sales_rep_id", "customer_profiles", ["assigned_sales_rep_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("payment_methods"):
        op.create_table(
            "payment_methods",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("code", sa.String(32), nullable=False),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("requires_reference", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("requires_cash_session", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("allowed_currencies", sa.String(128), nullable=False, server_default="USD,PEN,EUR"),
            *timestamp_columns(),
            sa.UniqueConstraint("company_id", "code", name="uq_payment_methods_company_code")
        )
        op.create_index("ix_payment_methods_company_id", "payment_methods", ["company_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("payment_intents"):
        op.create_table(
            "payment_intents",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("provider", sa.String(32), nullable=False),
            sa.Column("amount", sa.Numeric(20, 6), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("provider_intent_id", sa.String(128), nullable=True),
            sa.Column("client_secret", sa.String(255), nullable=True),
            sa.Column("idempotency_key", sa.String(128), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            *timestamp_columns()
        )
        op.create_index("ix_payment_intents_company_id", "payment_intents", ["company_id"])
        op.create_index("ix_payment_intents_sale_id", "payment_intents", ["sale_id"])
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("payment_allocations"):
        op.create_table(
            "payment_allocations",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("payment_id", sa.Uuid(), sa.ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("allocated_amount", sa.Numeric(20, 6), nullable=False),
            *timestamp_columns()
        )
        op.create_index("ix_payment_allocations_company_id", "payment_allocations", ["company_id"])
        op.create_index("ix_payment_allocations_payment_id", "payment_allocations", ["payment_id"])
        op.create_index("ix_payment_allocations_sale_id", "payment_allocations", ["sale_id"])
    if op.get_bind().dialect.name == "postgresql":
        for table in ("categories", "product_profiles", "product_variants", "product_barcodes", "units_of_measure", "customer_profiles", "payment_methods", "payment_intents", "payment_allocations"):
            policy = f"{table}_tenant_policy"
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table}"')
            op.execute(f'CREATE POLICY "{policy}" ON "{table}" USING (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid) WITH CHECK (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid)')


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table in ("payment_allocations", "payment_intents", "payment_methods", "customer_profiles", "units_of_measure", "product_barcodes", "product_variants", "product_profiles", "categories"):
        if inspector.has_table(table):
            op.drop_table(table)
