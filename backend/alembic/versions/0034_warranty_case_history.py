from alembic import op
import sqlalchemy as sa

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sale_lines", sa.Column("warranty_months_snapshot", sa.Integer(), nullable=True))
    op.add_column("sale_lines", sa.Column("warranty_policy_snapshot", sa.Text(), nullable=True))
    op.add_column("product_warranty_claims", sa.Column("sale_line_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("product_warranty_claims", sa.Column("quantity", sa.Numeric(20, 6), nullable=False, server_default="1"))
    op.add_column("product_warranty_claims", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("product_warranty_claims", sa.Column("warranty_until", sa.DateTime(timezone=True)))
    op.add_column("product_warranty_claims", sa.Column("assigned_to", sa.Uuid()))
    op.add_column("product_warranty_claims", sa.Column("diagnosis", sa.Text()))
    op.add_column("product_warranty_claims", sa.Column("resolution", sa.Text()))
    op.add_column("product_warranty_claims", sa.Column("policy_snapshot", sa.Text()))
    op.add_column("product_warranty_claims", sa.Column("history_json", sa.Text(), nullable=False, server_default="[]"))
    with op.batch_alter_table("product_warranty_claims") as batch:
        batch.create_foreign_key("fk_warranty_claim_sale_line", "sale_lines", ["sale_line_id"], ["id"])
        batch.create_foreign_key("fk_warranty_claim_assignee", "users", ["assigned_to"], ["id"])


def downgrade():
    raise RuntimeError("Las políticas de garantía y sus expedientes deben conservarse.")
