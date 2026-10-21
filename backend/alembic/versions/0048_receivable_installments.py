from alembic import op
import sqlalchemy as sa

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("receivable_schedules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("sale_id", sa.Uuid(), sa.ForeignKey("sales.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("active_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opening_balance", sa.Numeric(20, 6), nullable=False),
        sa.Column("schedule_json", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "sale_id", name="uq_receivable_schedule_sale"),
        sa.CheckConstraint("opening_balance > 0", name="ck_receivable_schedule_balance"))
    op.create_table("receivable_installment_allocations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("allocation_id", sa.Uuid(), sa.ForeignKey("payment_allocations.id"), nullable=False, index=True),
        sa.Column("schedule_id", sa.Uuid(), sa.ForeignKey("receivable_schedules.id"), nullable=False, index=True),
        sa.Column("schedule_version", sa.Integer(), nullable=False),
        sa.Column("installment_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("allocation_id", "schedule_id", "schedule_version", "installment_id", name="uq_receivable_installment_allocation"),
        sa.CheckConstraint("amount > 0", name="ck_receivable_installment_allocation_amount"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("receivable_schedules", "receivable_installment_allocations"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Los cronogramas y las aplicaciones de cobros deben conservarse.")
