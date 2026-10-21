from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales", sa.Column("warehouse_id", sa.Uuid(), nullable=True))
    op.add_column("sales", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("sales", sa.Column("is_credit", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table("idempotency_records",
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("operation", sa.String(128), primary_key=True),
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("document_sequences",
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("series", sa.String(16), primary_key=True),
        sa.Column("value", sa.Integer(), nullable=False))
    op.execute("INSERT INTO document_sequences (company_id, series, value) SELECT company_id, series, MAX(number) FROM sales GROUP BY company_id, series")
    op.create_table("payment_refunds",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("payment_id", sa.Uuid(), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_payment_refunds_company_id", "payment_refunds", ["company_id"])
    op.create_index("ix_payment_refunds_payment_id", "payment_refunds", ["payment_id"])


def downgrade():
    op.drop_table("payment_refunds")
    op.drop_table("document_sequences")
    op.drop_table("idempotency_records")
    with op.batch_alter_table("sales") as batch:
        batch.drop_column("is_credit")
        batch.drop_column("version")
        batch.drop_column("warehouse_id")
