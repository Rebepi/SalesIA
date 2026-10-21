from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0026"
down_revision: Union[str, None] = "0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def add_column_if_missing(table: str, column: sa.Column) -> None:
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in columns:
        op.add_column(table, column)


def upgrade() -> None:
    add_column_if_missing("quotations", sa.Column("special_conditions", sa.Text(), nullable=True))
    add_column_if_missing("quotations", sa.Column("seller_id", sa.Uuid(), nullable=True))
    add_column_if_missing("quotations", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("quotations", sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("quotations", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True))
    add_column_if_missing("quotations", sa.Column("delivery_channel", sa.String(length=32), nullable=True))
    add_column_if_missing("quotations", sa.Column("delivery_recipient", sa.String(length=255), nullable=True))
    add_column_if_missing("quotations", sa.Column("communication_log_json", sa.Text(), nullable=False, server_default="[]"))
    add_column_if_missing("orders", sa.Column("picking_json", sa.Text(), nullable=False, server_default="{}"))
    add_column_if_missing("product_profiles", sa.Column("supplier_id", sa.Uuid(), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("brand", sa.String(length=128), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("image_url", sa.String(length=512), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("length_cm", sa.Numeric(12, 3), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("width_cm", sa.Numeric(12, 3), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("height_cm", sa.Numeric(12, 3), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("weight_kg", sa.Numeric(12, 3), nullable=True))
    add_column_if_missing("product_profiles", sa.Column("tracking_mode", sa.String(length=16), nullable=False, server_default="NONE"))


def downgrade() -> None:
    groups = {
        "quotations": ["communication_log_json", "delivery_recipient", "delivery_channel", "accepted_at", "opened_at", "sent_at", "seller_id", "special_conditions"],
        "orders": ["picking_json"],
        "product_profiles": ["tracking_mode", "weight_kg", "height_cm", "width_cm", "length_cm", "image_url", "brand", "supplier_id"]
    }
    for table, names in groups.items():
        columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
        for name in names:
            if name in columns:
                op.drop_column(table, name)
