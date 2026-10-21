from alembic import op
import sqlalchemy as sa

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sale_lines", sa.Column("return_policy_snapshot", sa.Text(), nullable=True))


def downgrade():
    raise RuntimeError("Las condiciones de devolución ofrecidas al vender deben conservarse.")
