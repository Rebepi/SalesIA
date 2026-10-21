from alembic import op
import sqlalchemy as sa

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales", sa.Column("order_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("sales", sa.Column("fulfillment_status", sa.String(32), nullable=False, server_default="pending"))
    op.add_column("sale_lines", sa.Column("order_line_number", sa.Integer(), nullable=True))
    with op.batch_alter_table("sales") as batch:
        batch.create_foreign_key("fk_sales_source_order", "orders", ["order_id"], ["id"], ondelete="RESTRICT")
    op.execute("UPDATE sales SET fulfillment_status = 'delivered' WHERE status IN ('confirmed', 'paid', 'refunded')")


def downgrade():
    raise RuntimeError("Los vínculos entre pedidos, ventas y cumplimiento deben conservarse.")
