from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("company_settings",
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("values_json", sa.Text(), nullable=False))


def downgrade():
    op.drop_table("company_settings")
