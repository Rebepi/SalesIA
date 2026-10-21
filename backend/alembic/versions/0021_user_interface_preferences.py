from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("font_scale", sa.String(length=16), nullable=False, server_default="standard"))
    op.add_column("users", sa.Column("contrast_mode", sa.String(length=16), nullable=False, server_default="standard"))
    op.add_column("users", sa.Column("default_page_size", sa.Integer(), nullable=False, server_default="25"))
    op.add_column("users", sa.Column("sidebar_mode", sa.String(length=16), nullable=False, server_default="expanded"))
    op.add_column("users", sa.Column("accessible_tables", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("toast_position", sa.String(length=32), nullable=False, server_default="bottom-right"))


def downgrade() -> None:
    op.drop_column("users", "toast_position")
    op.drop_column("users", "accessible_tables")
    op.drop_column("users", "sidebar_mode")
    op.drop_column("users", "default_page_size")
    op.drop_column("users", "contrast_mode")
    op.drop_column("users", "font_scale")
