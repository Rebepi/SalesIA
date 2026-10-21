from alembic import op
import sqlalchemy as sa

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("customer_contacts", "customer_addresses"):
        op.add_column(table, sa.Column("valid_from", sa.Date(), nullable=True))
        op.add_column(table, sa.Column("valid_until", sa.Date(), nullable=True))
        op.add_column(table, sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        op.add_column(table, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("customer_contacts", sa.Column("purpose", sa.String(32), nullable=False, server_default="general"))
    op.add_column("customer_contacts", sa.Column("can_purchase", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("customer_contacts", sa.Column("can_receive", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    raise RuntimeError("Las vigencias y autorizaciones de contactos deben conservarse.")
