from alembic import op
import sqlalchemy as sa

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("suppliers", sa.Column("qualification_status", sa.String(32), nullable=False, server_default="approved"))
    op.add_column("suppliers", sa.Column("qualification_until", sa.Date(), nullable=True))
    op.add_column("suppliers", sa.Column("qualification_history_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("suppliers", sa.Column("qualification_documents_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("suppliers", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    raise RuntimeError("La evaluación de proveedores debe conservarse.")
