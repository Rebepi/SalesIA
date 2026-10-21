from alembic import op
import sqlalchemy as sa

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("supply_lines", sa.Column("cancelled_quantity", sa.Numeric(20, 6), nullable=False, server_default="0"))
    op.create_table("supply_document_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("supply_documents.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_email", sa.String(255), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "document_id", "version", name="uq_supply_revision_version"))
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "supply_document_revisions" ENABLE ROW LEVEL SECURITY')
        op.execute('ALTER TABLE "supply_document_revisions" FORCE ROW LEVEL SECURITY')
        op.execute("CREATE POLICY tenant_scope ON supply_document_revisions USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    raise RuntimeError("El historial y las cancelaciones de compras deben conservarse.")
