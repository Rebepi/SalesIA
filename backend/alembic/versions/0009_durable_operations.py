from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    for name, column in (
        ("requested_by", sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("users.id"))),
        ("payload_json", sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}")),
        ("lease_until", sa.Column("lease_until", sa.DateTime(timezone=True))),
        ("attempts", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0")),
        ("cancel_requested", sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false())),
    ):
        op.add_column("jobs", column)
    op.add_column("backup_snapshots", sa.Column("artifact_path", sa.Text(), nullable=False, server_default=""))
    op.add_column("backup_snapshots", sa.Column("nonce", sa.String(64), nullable=False, server_default=""))
    op.add_column("backup_snapshots", sa.Column("source_revision", sa.String(128), nullable=False, server_default="unknown"))
    op.create_table("operation_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "key"))
    op.create_index("ix_operation_settings_company_id", "operation_settings", ["company_id"])
    op.create_table("notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_notifications_company_id", "notifications", ["company_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_table("upload_grants",
        sa.Column("attachment_id", sa.Uuid(), sa.ForeignKey("attachments.id"), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expected_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)))
    op.create_table("webhook_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("company_id", sa.Uuid(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("connection_id", sa.String(128), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "connection_id", "event_id"))
    op.create_index("ix_webhook_receipts_company_id", "webhook_receipts", ["company_id"])
    if op.get_bind().dialect.name == "postgresql":
        for table in ("operation_settings", "notifications", "webhook_receipts"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f"CREATE POLICY tenant_scope ON {table} USING (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid) WITH CHECK (company_id = NULLIF(current_setting('app.current_company_id', true), '')::uuid)")


def downgrade():
    for table in ("webhook_receipts", "upload_grants", "notifications", "operation_settings"):
        op.drop_table(table)
    with op.batch_alter_table("backup_snapshots") as batch:
        batch.drop_column("source_revision")
        batch.drop_column("nonce")
        batch.drop_column("artifact_path")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("cancel_requested")
        batch.drop_column("attempts")
        batch.drop_column("lease_until")
        batch.drop_column("payload_json")
        batch.drop_column("requested_by")
