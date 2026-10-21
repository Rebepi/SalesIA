from alembic import op
import sqlalchemy as sa

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("delivery_vehicles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("max_weight_kg", sa.Numeric(20, 6), nullable=False),
        sa.Column("max_volume_m3", sa.Numeric(20, 6), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_delivery_vehicle_code"),
        sa.CheckConstraint("max_weight_kg > 0 AND max_volume_m3 > 0", name="ck_delivery_vehicle_capacity"))
    op.create_table("delivery_routes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False, index=True),
        sa.Column("zone", sa.String(128), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), sa.ForeignKey("delivery_vehicles.id"), nullable=False, index=True),
        sa.Column("responsible_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("warehouse_id", sa.Uuid(), sa.ForeignKey("warehouses.id"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("stops_json", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_delivery_route_code"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("delivery_vehicles", "delivery_routes"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Los recorridos y sus manifiestos deben conservarse.")
