from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0019'
down_revision: Union[str, None] = '0018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'inventory_quarantines',
        'reason',
        existing_type=sa.String(length=64),
        type_=sa.String(length=255),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'inventory_quarantines',
        'reason',
        existing_type=sa.String(length=255),
        type_=sa.String(length=64),
        existing_nullable=False
    )
