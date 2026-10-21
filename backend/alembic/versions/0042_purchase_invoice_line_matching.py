from alembic import op
import sqlalchemy as sa

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("purchase_invoice_matches", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("purchase_invoice_matches", sa.Column("lines_snapshot_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("purchase_invoice_matches", sa.Column("validation_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("purchase_invoice_matches", sa.Column("policy_snapshot_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("supplier_payables", sa.Column("invoice_match_id", sa.Uuid(), nullable=True))
    with op.batch_alter_table("supplier_payables") as batch:
        batch.create_foreign_key("fk_payable_invoice_match", "purchase_invoice_matches", ["invoice_match_id"], ["id"], ondelete="RESTRICT")
        batch.create_unique_constraint("uq_payable_invoice_match", ["invoice_match_id"])


def downgrade():
    raise RuntimeError("Las conciliaciones y obligaciones vinculadas deben conservarse.")
