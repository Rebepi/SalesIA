from alembic import op
import sqlalchemy as sa

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def identifiers():
    return [sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True)]


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]


def upgrade():
    op.add_column("collaboration_approvals", sa.Column("document_hash", sa.String(64)))
    op.add_column("collaboration_approvals", sa.Column("policy_snapshot_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("collaboration_approvals", sa.Column("stage_index", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("collaboration_approvals", sa.Column("due_at", sa.DateTime(timezone=True)))
    op.create_table("business_approval_policies", *identifiers(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False), *timestamps(),
        sa.UniqueConstraint("company_id", "code", name="uq_approval_policy_code"))
    op.create_table("business_approval_votes", *identifiers(),
        sa.Column("approval_id", sa.Uuid(), sa.ForeignKey("collaboration_approvals.id"), nullable=False, index=True),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("represented_principal_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False), *timestamps(),
        sa.UniqueConstraint("approval_id", "stage", "actor_id", name="uq_approval_vote_actor_stage"),
        sa.UniqueConstraint("approval_id", "stage", "represented_principal_id", name="uq_approval_vote_principal_stage"))
    op.create_table("business_approval_delegations", *identifiers(),
        sa.Column("principal_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("delegate_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)), *timestamps())
    if op.get_bind().dialect.name == "postgresql":
        for table in ("business_approval_policies", "business_approval_votes", "business_approval_delegations"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Las decisiones y delegaciones deben conservarse.")
