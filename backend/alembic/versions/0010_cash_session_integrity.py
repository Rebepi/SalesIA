from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cash_sessions", sa.Column("terminal_code", sa.String(32), nullable=True))
    op.execute("UPDATE cash_sessions SET terminal_code = 'LEGACY-' || LEFT(id::text, 8) WHERE terminal_code IS NULL")
    op.alter_column("cash_sessions", "terminal_code", nullable=False)
    op.create_index("uq_cash_sessions_open_terminal", "cash_sessions", ["company_id", "terminal_code"], unique=True, postgresql_where=sa.text("status = 'open'"))


def downgrade():
    op.drop_index("uq_cash_sessions_open_terminal", table_name="cash_sessions")
    op.drop_column("cash_sessions", "terminal_code")
