from alembic import op
import sqlalchemy as sa


revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "collaboration_tasks" not in tables:
        op.create_table("collaboration_tasks",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("assignee_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True, index=True),
            sa.Column("creator_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("priority", sa.String(32), nullable=False),
            sa.Column("resource_type", sa.String(64), nullable=True),
            sa.Column("resource_id", sa.Uuid(), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("resolution_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if "collaboration_comments" not in tables:
        op.create_table("collaboration_comments",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
            sa.Column("resource_type", sa.String(64), nullable=False, index=True),
            sa.Column("resource_id", sa.Uuid(), nullable=False, index=True),
            sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("sanitized_content", sa.Text(), nullable=False),
            sa.Column("mentions_json", sa.Text(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("is_edited", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    if "collaboration_approvals" not in tables:
        op.create_table("collaboration_approvals",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
            sa.Column("resource_type", sa.String(64), nullable=False, index=True),
            sa.Column("resource_id", sa.Uuid(), nullable=False, index=True),
            sa.Column("document_version", sa.Integer(), nullable=False),
            sa.Column("policy_name", sa.String(128), nullable=False),
            sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("decided_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("decision_reason", sa.Text(), nullable=True),
            sa.Column("evidence_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))
    if "saved_views" not in tables:
        op.create_table("saved_views",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("resource_type", sa.String(64), nullable=False, index=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("schema_version", sa.Integer(), nullable=False),
            sa.Column("config_json", sa.Text(), nullable=False),
            sa.Column("is_shared", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("company_id", "user_id", "resource_type", "name", name="uq_user_saved_view"))
    if "notification_preferences" not in tables:
        op.create_table("notification_preferences",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("channel", sa.String(32), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("schedule_start", sa.String(8), nullable=True),
            sa.Column("schedule_end", sa.String(8), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("company_id", "user_id", "category", "channel", name="uq_user_notif_pref"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("collaboration_tasks", "collaboration_comments", "collaboration_approvals", "saved_views", "notification_preferences"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f'DROP POLICY IF EXISTS tenant_scope ON "{table}"')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("La migración conserva tareas, comentarios y decisiones. Restaura una copia de respaldo para revertir el esquema.")
