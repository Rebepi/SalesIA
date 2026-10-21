from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0018'
down_revision: Union[str, None] = '0017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tenant_tables = [
    'categories', 'collaboration_approvals', 'collaboration_comments', 'collaboration_tasks',
    'coupons', 'credit_notes', 'customer_activities', 'customer_addresses', 'customer_contacts',
    'customer_credit_movements', 'customer_import_batches', 'customer_loyalty_ledger', 'customer_notes',
    'customer_opportunities', 'customer_profiles', 'customer_segments', 'dead_letter_jobs',
    'delivery_incidents', 'delivery_shipments', 'delivery_tracking_events', 'external_entity_mappings',
    'external_notification_intents', 'external_sync_cursors', 'finance_reconciliation_items',
    'finance_reconciliations', 'inbox_events', 'integration_connections', 'landed_cost_adjustments',
    'notification_preferences', 'payment_allocations', 'payment_disputes', 'payment_intents',
    'payment_methods', 'payment_reversals', 'price_list_items', 'price_lists', 'product_attachments',
    'product_barcodes', 'product_kit_items', 'product_price_history', 'product_profiles',
    'product_variants', 'product_volume_tiers', 'product_warranty_claims', 'promotions',
    'proof_of_deliveries', 'purchase_invoice_matches', 'sales_returns', 'sales_targets', 'saved_views',
    'transfer_proofs', 'unit_conversions', 'units_of_measure', 'webhook_subscriptions'
]


def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('ui_theme', sa.String(length=16), nullable=False, server_default='light'))
    op.add_column('users', sa.Column('ui_density', sa.String(length=16), nullable=False, server_default='comfortable'))
    op.add_column('users', sa.Column('reduced_motion', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('integration_connections', sa.Column('category', sa.String(length=64), nullable=False, server_default='payments'))
    op.add_column('integration_connections', sa.Column('mode', sa.String(length=16), nullable=False, server_default='test'))
    op.add_column('integration_connections', sa.Column('status', sa.String(length=32), nullable=False, server_default='connected'))
    op.add_column('integration_connections', sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True))
    op.add_column('integration_connections', sa.Column('last_error', sa.Text(), nullable=True))
    op.add_column('integration_connections', sa.Column('latency_ms', sa.Integer(), nullable=True))
    op.add_column('integration_connections', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column('attachments', sa.Column('scan_status', sa.String(length=32), nullable=False, server_default='clean'))
    op.add_column('attachments', sa.Column('classification', sa.String(length=32), nullable=False, server_default='internal'))
    op.add_column('attachments', sa.Column('owner_id', sa.Uuid(), nullable=True))
    op.add_column('commission_settlements', sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('commission_settlements', sa.Column('rules_version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('commission_settlements', sa.Column('prior_adjustments', sa.Numeric(precision=20, scale=6), nullable=False, server_default='0.000000'))
    op.add_column('commission_settlements', sa.Column('notes', sa.Text(), nullable=True))
    op.create_index(op.f('ix_credit_note_lines_product_id'), 'credit_note_lines', ['product_id'], unique=False)
    op.create_index(op.f('ix_credit_notes_branch_id'), 'credit_notes', ['branch_id'], unique=False)
    op.create_index(op.f('ix_credit_notes_return_id'), 'credit_notes', ['return_id'], unique=False)
    op.create_index(op.f('ix_customer_credit_movements_reference_id'), 'customer_credit_movements', ['reference_id'], unique=False)
    op.create_index(op.f('ix_inventory_alerts_alert_type'), 'inventory_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_inventory_alerts_company_id'), 'inventory_alerts', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_alerts_dedup_hash'), 'inventory_alerts', ['dedup_hash'], unique=False)
    op.create_index(op.f('ix_inventory_alerts_product_id'), 'inventory_alerts', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_alerts_warehouse_id'), 'inventory_alerts', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_location_stocks_company_id'), 'inventory_location_stocks', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_location_stocks_location_id'), 'inventory_location_stocks', ['location_id'], unique=False)
    op.create_index(op.f('ix_inventory_location_stocks_product_id'), 'inventory_location_stocks', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_location_stocks_warehouse_id'), 'inventory_location_stocks', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_lots_company_id'), 'inventory_lots', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_lots_lot_code'), 'inventory_lots', ['lot_code'], unique=False)
    op.create_index(op.f('ix_inventory_lots_product_id'), 'inventory_lots', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lines_company_id'), 'inventory_picking_lines', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lines_picking_list_id'), 'inventory_picking_lines', ['picking_list_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lines_product_id'), 'inventory_picking_lines', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lists_company_id'), 'inventory_picking_lists', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lists_sale_id'), 'inventory_picking_lists', ['sale_id'], unique=False)
    op.create_index(op.f('ix_inventory_picking_lists_warehouse_id'), 'inventory_picking_lists', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_quarantines_company_id'), 'inventory_quarantines', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_quarantines_product_id'), 'inventory_quarantines', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_quarantines_warehouse_id'), 'inventory_quarantines', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_reconciliations_company_id'), 'inventory_reconciliations', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_reconciliations_product_id'), 'inventory_reconciliations', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_reconciliations_warehouse_id'), 'inventory_reconciliations', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_reservations_company_id'), 'inventory_reservations', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_reservations_document_id'), 'inventory_reservations', ['document_id'], unique=False)
    op.create_index(op.f('ix_inventory_reservations_product_id'), 'inventory_reservations', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_reservations_warehouse_id'), 'inventory_reservations', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_serials_company_id'), 'inventory_serials', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_serials_product_id'), 'inventory_serials', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_serials_serial_number'), 'inventory_serials', ['serial_number'], unique=False)
    op.create_index(op.f('ix_inventory_serials_warehouse_id'), 'inventory_serials', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_stock_rules_company_id'), 'inventory_stock_rules', ['company_id'], unique=False)
    op.create_index(op.f('ix_inventory_stock_rules_product_id'), 'inventory_stock_rules', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_stock_rules_warehouse_id'), 'inventory_stock_rules', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_valuation_settings_company_id'), 'inventory_valuation_settings', ['company_id'], unique=False)
    op.add_column('notifications', sa.Column('priority', sa.String(length=32), nullable=False, server_default='normal'))
    op.add_column('notifications', sa.Column('category', sa.String(length=64), nullable=False, server_default='general'))
    op.add_column('notifications', sa.Column('resource_type', sa.String(length=64), nullable=True))
    op.add_column('notifications', sa.Column('resource_id', sa.Uuid(), nullable=True))
    op.add_column('orders', sa.Column('delivery_terms', sa.String(length=255), nullable=True))
    op.add_column('orders', sa.Column('customer_po_number', sa.String(length=64), nullable=True))
    op.add_column('orders', sa.Column('attachments_json', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('orders', sa.Column('reservation_expires_at', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_physical_count_lines_company_id'), 'physical_count_lines', ['company_id'], unique=False)
    op.create_index(op.f('ix_physical_count_lines_product_id'), 'physical_count_lines', ['product_id'], unique=False)
    op.create_index(op.f('ix_physical_count_lines_session_id'), 'physical_count_lines', ['session_id'], unique=False)
    op.create_index(op.f('ix_physical_count_sessions_company_id'), 'physical_count_sessions', ['company_id'], unique=False)
    op.create_index(op.f('ix_physical_count_sessions_warehouse_id'), 'physical_count_sessions', ['warehouse_id'], unique=False)
    op.add_column('quotations', sa.Column('delivery_terms', sa.String(length=255), nullable=True))
    op.add_column('quotations', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('sales_representatives', sa.Column('code', sa.String(length=64), nullable=True))
    op.add_column('sales_representatives', sa.Column('branch_id', sa.Uuid(), nullable=True))
    op.add_column('sales_representatives', sa.Column('team', sa.String(length=128), nullable=True))
    op.add_column('sales_representatives', sa.Column('supervisor_id', sa.Uuid(), nullable=True))
    op.alter_column('sales_representatives', 'user_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.create_foreign_key(op.f('fk_sales_representatives_branch_id_branches'), 'sales_representatives', 'branches', ['branch_id'], ['id'])
    op.create_foreign_key(op.f('fk_sales_representatives_supervisor_id_users'), 'sales_representatives', 'users', ['supervisor_id'], ['id'])
    op.add_column('suppliers', sa.Column('contact_name', sa.String(length=255), nullable=True))
    op.add_column('suppliers', sa.Column('payment_terms_days', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('suppliers', sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'))
    op.add_column('suppliers', sa.Column('bank_name', sa.String(length=128), nullable=True))
    op.add_column('suppliers', sa.Column('bank_account', sa.String(length=64), nullable=True))
    op.add_column('suppliers', sa.Column('notes', sa.Text(), nullable=True))
    if op.get_bind().dialect.name == 'postgresql':
        inspector = sa.inspect(op.get_bind())
        for table in tenant_tables:
            if not inspector.has_table(table):
                continue
            policy = f'{table}_tenant_policy'
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table}"')
            op.execute(f'CREATE POLICY "{policy}" ON "{table}" USING (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid) WITH CHECK (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid)')


def downgrade() -> None:
    if op.get_bind().dialect.name == 'postgresql':
        inspector = sa.inspect(op.get_bind())
        for table in reversed(tenant_tables):
            if not inspector.has_table(table):
                continue
            policy = f'{table}_tenant_policy'
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{table}"')
            op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
    op.drop_column('integration_connections', 'updated_at')
    op.drop_column('integration_connections', 'latency_ms')
    op.drop_column('integration_connections', 'last_error')
    op.drop_column('integration_connections', 'last_sync')
    op.drop_column('integration_connections', 'status')
    op.drop_column('integration_connections', 'mode')
    op.drop_column('integration_connections', 'category')
    op.drop_column('users', 'reduced_motion')
    op.drop_column('users', 'ui_density')
    op.drop_column('users', 'ui_theme')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'full_name')
    op.drop_column('suppliers', 'notes')
    op.drop_column('suppliers', 'bank_account')
    op.drop_column('suppliers', 'bank_name')
    op.drop_column('suppliers', 'currency')
    op.drop_column('suppliers', 'payment_terms_days')
    op.drop_column('suppliers', 'contact_name')
    op.drop_constraint(op.f('fk_sales_representatives_supervisor_id_users'), 'sales_representatives', type_='foreignkey')
    op.drop_constraint(op.f('fk_sales_representatives_branch_id_branches'), 'sales_representatives', type_='foreignkey')
    op.alter_column('sales_representatives', 'user_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('sales_representatives', 'supervisor_id')
    op.drop_column('sales_representatives', 'team')
    op.drop_column('sales_representatives', 'branch_id')
    op.drop_column('sales_representatives', 'code')
    op.drop_column('quotations', 'notes')
    op.drop_column('quotations', 'delivery_terms')
    op.drop_index(op.f('ix_physical_count_sessions_warehouse_id'), table_name='physical_count_sessions')
    op.drop_index(op.f('ix_physical_count_sessions_company_id'), table_name='physical_count_sessions')
    op.drop_index(op.f('ix_physical_count_lines_session_id'), table_name='physical_count_lines')
    op.drop_index(op.f('ix_physical_count_lines_product_id'), table_name='physical_count_lines')
    op.drop_index(op.f('ix_physical_count_lines_company_id'), table_name='physical_count_lines')
    op.drop_column('orders', 'reservation_expires_at')
    op.drop_column('orders', 'attachments_json')
    op.drop_column('orders', 'customer_po_number')
    op.drop_column('orders', 'delivery_terms')
    op.drop_column('notifications', 'resource_id')
    op.drop_column('notifications', 'resource_type')
    op.drop_column('notifications', 'category')
    op.drop_column('notifications', 'priority')
    op.drop_index(op.f('ix_inventory_valuation_settings_company_id'), table_name='inventory_valuation_settings')
    op.drop_index(op.f('ix_inventory_stock_rules_warehouse_id'), table_name='inventory_stock_rules')
    op.drop_index(op.f('ix_inventory_stock_rules_product_id'), table_name='inventory_stock_rules')
    op.drop_index(op.f('ix_inventory_stock_rules_company_id'), table_name='inventory_stock_rules')
    op.drop_index(op.f('ix_inventory_serials_warehouse_id'), table_name='inventory_serials')
    op.drop_index(op.f('ix_inventory_serials_serial_number'), table_name='inventory_serials')
    op.drop_index(op.f('ix_inventory_serials_product_id'), table_name='inventory_serials')
    op.drop_index(op.f('ix_inventory_serials_company_id'), table_name='inventory_serials')
    op.drop_index(op.f('ix_inventory_reservations_warehouse_id'), table_name='inventory_reservations')
    op.drop_index(op.f('ix_inventory_reservations_product_id'), table_name='inventory_reservations')
    op.drop_index(op.f('ix_inventory_reservations_document_id'), table_name='inventory_reservations')
    op.drop_index(op.f('ix_inventory_reservations_company_id'), table_name='inventory_reservations')
    op.drop_index(op.f('ix_inventory_reconciliations_warehouse_id'), table_name='inventory_reconciliations')
    op.drop_index(op.f('ix_inventory_reconciliations_product_id'), table_name='inventory_reconciliations')
    op.drop_index(op.f('ix_inventory_reconciliations_company_id'), table_name='inventory_reconciliations')
    op.drop_index(op.f('ix_inventory_quarantines_warehouse_id'), table_name='inventory_quarantines')
    op.drop_index(op.f('ix_inventory_quarantines_product_id'), table_name='inventory_quarantines')
    op.drop_index(op.f('ix_inventory_quarantines_company_id'), table_name='inventory_quarantines')
    op.drop_index(op.f('ix_inventory_picking_lists_warehouse_id'), table_name='inventory_picking_lists')
    op.drop_index(op.f('ix_inventory_picking_lists_sale_id'), table_name='inventory_picking_lists')
    op.drop_index(op.f('ix_inventory_picking_lists_company_id'), table_name='inventory_picking_lists')
    op.drop_index(op.f('ix_inventory_picking_lines_product_id'), table_name='inventory_picking_lines')
    op.drop_index(op.f('ix_inventory_picking_lines_picking_list_id'), table_name='inventory_picking_lines')
    op.drop_index(op.f('ix_inventory_picking_lines_company_id'), table_name='inventory_picking_lines')
    op.drop_index(op.f('ix_inventory_lots_product_id'), table_name='inventory_lots')
    op.drop_index(op.f('ix_inventory_lots_lot_code'), table_name='inventory_lots')
    op.drop_index(op.f('ix_inventory_lots_company_id'), table_name='inventory_lots')
    op.drop_index(op.f('ix_inventory_location_stocks_warehouse_id'), table_name='inventory_location_stocks')
    op.drop_index(op.f('ix_inventory_location_stocks_product_id'), table_name='inventory_location_stocks')
    op.drop_index(op.f('ix_inventory_location_stocks_location_id'), table_name='inventory_location_stocks')
    op.drop_index(op.f('ix_inventory_location_stocks_company_id'), table_name='inventory_location_stocks')
    op.drop_index(op.f('ix_inventory_alerts_warehouse_id'), table_name='inventory_alerts')
    op.drop_index(op.f('ix_inventory_alerts_product_id'), table_name='inventory_alerts')
    op.drop_index(op.f('ix_inventory_alerts_dedup_hash'), table_name='inventory_alerts')
    op.drop_index(op.f('ix_inventory_alerts_company_id'), table_name='inventory_alerts')
    op.drop_index(op.f('ix_inventory_alerts_alert_type'), table_name='inventory_alerts')
    op.drop_index(op.f('ix_customer_credit_movements_reference_id'), table_name='customer_credit_movements')
    op.drop_index(op.f('ix_credit_notes_return_id'), table_name='credit_notes')
    op.drop_index(op.f('ix_credit_notes_branch_id'), table_name='credit_notes')
    op.drop_index(op.f('ix_credit_note_lines_product_id'), table_name='credit_note_lines')
    op.drop_column('commission_settlements', 'notes')
    op.drop_column('commission_settlements', 'prior_adjustments')
    op.drop_column('commission_settlements', 'rules_version')
    op.drop_column('commission_settlements', 'paid_at')
    op.drop_column('attachments', 'owner_id')
    op.drop_column('attachments', 'classification')
    op.drop_column('attachments', 'scan_status')
