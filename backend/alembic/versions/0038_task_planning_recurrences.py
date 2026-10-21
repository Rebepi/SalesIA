from alembic import op
import sqlalchemy as sa

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("collaboration_tasks", sa.Column("parent_id", sa.Uuid(), nullable=True, index=True))
    op.add_column("collaboration_tasks", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("collaboration_tasks", sa.Column("checklist_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("collaboration_tasks", sa.Column("dependencies_json", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("collaboration_tasks", sa.Column("recurrence_id", sa.Uuid(), nullable=True, index=True))
    with op.batch_alter_table("collaboration_tasks") as batch:
        batch.create_foreign_key("fk_task_parent", "collaboration_tasks", ["parent_id"], ["id"], ondelete="RESTRICT")
    op.create_table("task_recurrences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("template_json", sa.Text(), nullable=False),
        sa.Column("schedule_json", sa.Text(), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("task_occurrences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("recurrence_id", sa.Uuid(), sa.ForeignKey("task_recurrences.id"), nullable=False, index=True),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("collaboration_tasks.id"), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.UniqueConstraint("recurrence_id", "due_at", name="uq_task_occurrence_due"))
    if op.get_bind().dialect.name == "postgresql":
        for table in ("task_recurrences", "task_occurrences"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("Las tareas periódicas y sus ocurrencias deben conservarse.")
