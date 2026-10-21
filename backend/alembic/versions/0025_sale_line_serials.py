from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("sale_lines")}
    if "serial_numbers_json" not in columns:
        op.add_column("sale_lines", sa.Column("serial_numbers_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("sale_lines")}
    if "serial_numbers_json" in columns:
        op.drop_column("sale_lines", "serial_numbers_json")
