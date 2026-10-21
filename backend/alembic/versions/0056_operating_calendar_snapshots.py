from alembic import op
import sqlalchemy as sa

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sales") as batch:
        batch.add_column(sa.Column("due_calendar_snapshot_json", sa.Text(), nullable=True))
    with op.batch_alter_table("delivery_windows") as batch:
        batch.add_column(sa.Column("calendar_snapshot_json", sa.Text(), nullable=True))


def downgrade():
    raise RuntimeError("Deben conservarse las condiciones de calendario pactadas en ventas y entregas.")
