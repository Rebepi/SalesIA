from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("quotation_number", sa.String(32), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("subtotal_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("tax_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("total_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("valid_until", sa.String(64), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("converted_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lines_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("quotation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_number", sa.String(32), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="confirmed"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("subtotal_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("tax_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("total_amount", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("stock_reserved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("lines_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("history_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )

    op.create_table(
        "cash_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initial_cash", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("expected_cash", sa.Numeric(20, 6), nullable=False, server_default="0.000000"),
        sa.Column("actual_cash", sa.Numeric(20, 6), nullable=True),
        sa.Column("difference_cash", sa.Numeric(20, 6), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("movements_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )


def downgrade() -> None:
    op.drop_table("cash_sessions")
    op.drop_table("orders")
    op.drop_table("quotations")
