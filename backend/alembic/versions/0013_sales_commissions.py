from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sales_representatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("territory", sa.String(128), nullable=False),
        sa.Column("monthly_quota", sa.Numeric(20, 6), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "user_id", name="uq_sales_representative_user")
    )
    op.add_column("sales", sa.Column("sales_rep_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales_representatives.id"), nullable=True))
    op.create_index("ix_sales_sales_rep_id", "sales", ["sales_rep_id"])
    op.create_table(
        "commission_settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("representative_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales_representatives.id"), nullable=False, index=True),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("gross_sales", sa.Numeric(20, 6), nullable=False),
        sa.Column("returns_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("net_sales", sa.Numeric(20, 6), nullable=False),
        sa.Column("target_quota", sa.Numeric(20, 6), nullable=False),
        sa.Column("commission_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("commission_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="calculated"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "representative_id", "period", name="uq_commission_settlement_period")
    )
    for table in ("sales_representatives", "commission_settlements"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY {table}_tenant_policy ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    op.drop_table("commission_settlements")
    op.drop_index("ix_sales_sales_rep_id", table_name="sales")
    op.drop_column("sales", "sales_rep_id")
    op.drop_table("sales_representatives")
