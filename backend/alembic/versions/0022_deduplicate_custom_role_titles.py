from typing import Sequence, Union

from alembic import op


revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked_roles AS (
            SELECT
                role.id,
                role.company_id,
                role.role_key,
                FIRST_VALUE(role.role_key) OVER (
                    PARTITION BY role.company_id, lower(btrim(role.title))
                    ORDER BY (
                        SELECT count(*)
                        FROM users
                        WHERE users.company_id = role.company_id
                          AND users.role = role.role_key
                    ) DESC, role.role_key
                ) AS canonical_role_key,
                ROW_NUMBER() OVER (
                    PARTITION BY role.company_id, lower(btrim(role.title))
                    ORDER BY (
                        SELECT count(*)
                        FROM users
                        WHERE users.company_id = role.company_id
                          AND users.role = role.role_key
                    ) DESC, role.role_key
                ) AS duplicate_position
            FROM custom_roles AS role
        )
        UPDATE users
        SET role = ranked_roles.canonical_role_key
        FROM ranked_roles
        WHERE users.company_id = ranked_roles.company_id
          AND users.role = ranked_roles.role_key
          AND ranked_roles.duplicate_position > 1
        """
    )
    op.execute(
        """
        WITH ranked_roles AS (
            SELECT
                role.id,
                ROW_NUMBER() OVER (
                    PARTITION BY role.company_id, lower(btrim(role.title))
                    ORDER BY (
                        SELECT count(*)
                        FROM users
                        WHERE users.company_id = role.company_id
                          AND users.role = role.role_key
                    ) DESC, role.role_key
                ) AS duplicate_position
            FROM custom_roles AS role
        )
        DELETE FROM custom_roles
        USING ranked_roles
        WHERE custom_roles.id = ranked_roles.id
          AND ranked_roles.duplicate_position > 1
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_custom_roles_company_normalized_title ON custom_roles (company_id, lower(btrim(title)))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_custom_roles_company_normalized_title")
