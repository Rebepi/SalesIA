from alembic import op
import sqlalchemy as sa

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cash_sessions", sa.Column("count_control_json", sa.Text(), nullable=False, server_default="{}"))


def downgrade():
    raise RuntimeError("Los arqueos y sus autorizaciones deben conservarse.")
