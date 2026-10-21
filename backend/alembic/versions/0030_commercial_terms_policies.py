from alembic import op
import sqlalchemy as sa

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales", sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("sales", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("commission_settlements", sa.Column("rules_snapshot_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("commission_settlements", sa.Column("calculation_detail_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade():
    raise RuntimeError("Los plazos y reglas históricas deben conservarse. Restaura un respaldo para revertir.")
