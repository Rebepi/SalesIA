"""Reinforce tenant RLS and make the audit chain append-only and ordered."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tenant_tables() -> list[str]:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT DISTINCT table_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND column_name = 'company_id'
              AND table_name <> 'alembic_version'
            ORDER BY table_name
            """
        )
    )
    auth_bootstrap_tables = {
        "users",
        "auth_sessions",
        "auth_challenges",
        "login_throttles",
        "auth_factors",
        "auth_recovery_codes",
        "auth_mail_outbox",
        "support_grants",
        "revoked_tokens",
    }
    return [row[0] for row in rows if row[0] not in auth_bootstrap_tables]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _tenant_tables():
        policies = bind.execute(
            sa.text("SELECT policyname FROM pg_policies WHERE schemaname='public' AND tablename=:table"),
            {"table": table},
        ).scalars().all()
        for policy in policies:
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'''CREATE POLICY "{table}_tenant_isolation" ON "{table}"
                USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)
                WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)'''
        )

    op.add_column("audit_logs", sa.Column("chain_sequence", sa.BigInteger(), nullable=True))
    op.execute(
        """
        WITH numbered AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY company_id
                       ORDER BY created_at ASC, id ASC
                   ) AS seq
            FROM audit_logs
        )
        UPDATE audit_logs AS target
        SET chain_sequence = numbered.seq
        FROM numbered
        WHERE target.id = numbered.id
        """
    )
    op.alter_column("audit_logs", "chain_sequence", nullable=False)
    op.create_unique_constraint(
        "uq_audit_logs_company_chain_sequence",
        "audit_logs",
        ["company_id", "chain_sequence"],
    )

    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")
    op.execute(
        """
        CREATE FUNCTION prevent_audit_log_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only' USING ERRCODE = '55000';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation()
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")
    op.drop_constraint("uq_audit_logs_company_chain_sequence", "audit_logs", type_="unique")
    op.drop_column("audit_logs", "chain_sequence")
