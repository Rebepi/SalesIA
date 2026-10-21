from alembic import op
import sqlalchemy as sa

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("delivery_windows",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("branch_id", sa.Uuid(), sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("identity_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("capacity > 0 AND ends_at > starts_at", name="ck_delivery_window_capacity_dates"))
    op.create_table("delivery_window_reservations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("delivery_id", sa.Uuid(), sa.ForeignKey("supply_documents.id"), nullable=False, index=True),
        sa.Column("window_id", sa.Uuid(), sa.ForeignKey("delivery_windows.id"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("authorized_people_json", sa.Text(), nullable=False),
        sa.Column("requirements_snapshot", sa.Text(), nullable=False),
        sa.Column("identity_required", sa.Boolean(), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_name", sa.String(255), nullable=True),
        sa.Column("checked_in_doc", sa.String(64), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "delivery_id", name="uq_delivery_window_reservation"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("delivery_windows", "delivery_window_reservations"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Las reservas y sus autorizaciones de retiro deben conservarse.")
