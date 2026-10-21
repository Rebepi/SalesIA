from alembic import op
import sqlalchemy as sa


revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_stock_rules", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("physical_count_lines", sa.Column("counted_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE physical_count_lines SET counted_at = updated_at WHERE session_id IN (SELECT id FROM physical_count_sessions WHERE status = 'approved')")


def downgrade():
    op.drop_column("physical_count_lines", "counted_at")
    op.drop_column("inventory_stock_rules", "is_active")
