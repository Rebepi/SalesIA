from alembic import op
import sqlalchemy as sa

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sales_targets") as batch:
        batch.drop_constraint("uq_sales_target_rep_period", type_="unique")
        batch.create_unique_constraint("uq_sales_target_currency_scope", ["company_id", "representative_id", "period", "target_type", "currency", "scope"])
    with op.batch_alter_table("sales") as batch:
        batch.add_column(sa.Column("commission_snapshot_json", sa.Text(), nullable=True))
    with op.batch_alter_table("commission_settlements") as batch:
        batch.add_column(sa.Column("currency", sa.String(3), nullable=True))
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("history_json", sa.Text(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("calculation_hash", sa.String(64), nullable=True))
        batch.add_column(sa.Column("payout_reference", sa.String(128), nullable=True))
        batch.add_column(sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True))
        batch.add_column(sa.Column("payable_amount", sa.Numeric(20, 6), nullable=False, server_default="0"))
        batch.add_column(sa.Column("carried_balance", sa.Numeric(20, 6), nullable=False, server_default="0"))
        batch.drop_constraint("uq_commission_settlement_period", type_="unique")
    bind = op.get_bind()
    security = []
    if bind.dialect.name == "postgresql":
        for table in ("commission_settlements", "companies"):
            flags = bind.execute(sa.text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = to_regclass(:table)"), {"table": table}).one()
            security.append((table, flags[0], flags[1]))
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("UPDATE commission_settlements SET currency = (SELECT base_currency FROM companies WHERE companies.id = commission_settlements.company_id)")
    op.execute("UPDATE commission_settlements SET payable_amount = commission_amount")
    for table, enabled, forced in security:
        if enabled:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        if forced:
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    with op.batch_alter_table("commission_settlements") as batch:
        batch.alter_column("currency", existing_type=sa.String(3), nullable=False)
        batch.create_unique_constraint("uq_commission_settlement_currency_period", ["company_id", "representative_id", "period", "currency"])
    op.create_table("commission_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("settlement_id", sa.Uuid(), sa.ForeignKey("commission_settlements.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("earned_base", sa.Numeric(20, 6), nullable=False),
        sa.Column("cumulative_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("settlement_id", "sale_id", name="uq_commission_entry_sale"))
    op.create_table("commission_observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("settlement_id", sa.Uuid(), sa.ForeignKey("commission_settlements.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("resolved_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if bind.dialect.name == "postgresql":
        for table in ("commission_entries", "commission_observations"):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Se debe conservar la atribución y conciliación de comisiones.")
