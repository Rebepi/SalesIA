from alembic import op
import sqlalchemy as sa

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("petty_cash_funds",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("cash_custody_accounts.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("policy_json", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "account_id", name="uq_petty_cash_account"))
    op.create_table("petty_cash_advances",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("fund_id", sa.Uuid(), sa.ForeignKey("petty_cash_funds.id"), nullable=False, index=True),
        sa.Column("beneficiary_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("policy_json", sa.Text(), nullable=False),
        sa.Column("settlement_json", sa.Text(), nullable=False),
        sa.Column("history_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_petty_cash_advance_code"),
        sa.CheckConstraint("amount > 0", name="ck_petty_cash_advance_positive"))
    with op.batch_alter_table("operating_expenses") as batch:
        batch.add_column(sa.Column("petty_cash_advance_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_expense_petty_cash_advance", "petty_cash_advances", ["petty_cash_advance_id"], ["id"])
        batch.create_index("ix_operating_expenses_petty_cash_advance_id", ["petty_cash_advance_id"])
    if op.get_bind().dialect.name == "postgresql":
        for table in ("petty_cash_funds", "petty_cash_advances"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Los fondos, anticipos y comprobantes rendidos deben conservarse.")
