from alembic import op
import sqlalchemy as sa

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sale_lines", sa.Column("fulfilled_quantity", sa.Numeric(20, 6), nullable=True))
    op.add_column("sale_lines", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sales_return_lines", sa.Column("sale_line_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("sales_return_lines", sa.Column("serial_numbers_json", sa.Text(), nullable=False, server_default="[]"))
    with op.batch_alter_table("sales_return_lines") as batch:
        batch.create_foreign_key("fk_return_source_sale_line", "sale_lines", ["sale_line_id"], ["id"], ondelete="RESTRICT")
    op.execute("UPDATE sale_lines SET fulfilled_quantity = quantity WHERE sale_id IN (SELECT id FROM sales WHERE status IN ('confirmed', 'paid', 'refunded'))")


def downgrade():
    raise RuntimeError("El cumplimiento y las devoluciones por línea deben conservarse.")
