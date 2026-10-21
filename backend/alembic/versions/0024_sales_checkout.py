from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("sales")}
    additions = (
        ("exchange_rate", sa.Numeric(20, 6), False, "1"),
        ("coupon_code", sa.String(64), True, None),
        ("notes", sa.Text(), True, None),
        ("delivery_address", sa.Text(), True, None),
        ("internal_observations", sa.Text(), True, None),
        ("pricing_explanation_json", sa.Text(), False, "[]")
    )
    for name, column_type, nullable, default in additions:
        if name not in columns:
            op.add_column("sales", sa.Column(name, column_type, nullable=nullable, server_default=default))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("sales")}
    for name in ("pricing_explanation_json", "internal_observations", "delivery_address", "notes", "coupon_code", "exchange_rate"):
        if name in columns:
            op.drop_column("sales", name)
