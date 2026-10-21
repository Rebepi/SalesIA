from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0016'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('supply_lines', sa.Column('damaged_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'))
    op.create_table(
        'warehouse_locations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('aisle', sa.String(length=32), nullable=False, server_default='A'),
        sa.Column('rack', sa.String(length=32), nullable=False, server_default='1'),
        sa.Column('shelf', sa.String(length=32), nullable=False, server_default='1'),
        sa.Column('bin', sa.String(length=32), nullable=False, server_default='1'),
        sa.Column('capacity_units', sa.Numeric(20, 6), nullable=False, server_default='1000.000000'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'warehouse_id', 'code', name='uq_location_warehouse_code')
    )
    op.create_index(op.f('ix_warehouse_locations_company_id'), 'warehouse_locations', ['company_id'], unique=False)
    op.create_index(op.f('ix_warehouse_locations_warehouse_id'), 'warehouse_locations', ['warehouse_id'], unique=False)

    op.create_table(
        'inventory_location_stocks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('warehouse_locations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'location_id', 'product_id', name='uq_location_stock_product')
    )

    op.create_table(
        'inventory_lots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('lot_code', sa.String(length=64), nullable=False),
        sa.Column('supplier_id', sa.Uuid(), sa.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('manufacture_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'product_id', 'lot_code', name='uq_lot_product_code')
    )
    op.create_index(op.f('ix_inventory_lots_expiration_date'), 'inventory_lots', ['expiration_date'], unique=False)

    op.create_table(
        'inventory_serials',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('serial_number', sa.String(length=128), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('warehouse_locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lot_id', sa.Uuid(), sa.ForeignKey('inventory_lots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='IN_STOCK'),
        sa.Column('current_doc_type', sa.String(length=32), nullable=True),
        sa.Column('current_doc_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'product_id', 'serial_number', name='uq_serial_product_number')
    )

    op.create_table(
        'inventory_stock_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('min_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('max_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('reorder_point', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('reorder_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'warehouse_id', 'product_id', name='uq_stock_rules_wh_prod')
    )

    op.create_table(
        'inventory_alerts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('alert_type', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False, server_default='WARNING'),
        sa.Column('message', sa.String(length=255), nullable=False),
        sa.Column('dedup_hash', sa.String(length=64), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responsible_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'dedup_hash', name='uq_inventory_alert_dedup')
    )

    op.create_table(
        'inventory_reservations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('document_type', sa.String(length=32), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('reserved_quantity', sa.Numeric(20, 6), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'document_type', 'document_id', 'product_id', name='uq_reservation_doc_prod')
    )

    op.create_table(
        'inventory_quarantines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Numeric(20, 6), nullable=False),
        sa.Column('reason', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='IN_QUARANTINE'),
        sa.Column('reference_doc_type', sa.String(length=32), nullable=True),
        sa.Column('reference_doc_id', sa.Uuid(), nullable=True),
        sa.Column('inspected_by', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'physical_count_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('count_code', sa.String(length=32), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='FULL'),
        sa.Column('scope_filter', sa.String(length=128), nullable=True),
        sa.Column('cutoff_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_blind', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending_count'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Uuid(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('approved_by', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'id', name='uq_count_session_company_id')
    )

    op.create_table(
        'physical_count_lines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('session_id', sa.Uuid(), sa.ForeignKey('physical_count_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('system_quantity_snapshot', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('counted_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('difference_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('unit_cost', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'product_id', name='uq_count_session_product')
    )

    op.create_table(
        'inventory_picking_lists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sale_id', sa.Uuid(), sa.ForeignKey('sales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('assigned_to', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'inventory_picking_lines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('picking_list_id', sa.Uuid(), sa.ForeignKey('inventory_picking_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('location_id', sa.Uuid(), sa.ForeignKey('warehouse_locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('lot_id', sa.Uuid(), sa.ForeignKey('inventory_lots.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expected_quantity', sa.Numeric(20, 6), nullable=False),
        sa.Column('picked_quantity', sa.Numeric(20, 6), nullable=False, server_default='0.000000'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'inventory_valuation_settings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=True),
        sa.Column('costing_method', sa.String(length=32), nullable=False, server_default='AVERAGE_WEIGHTED'),
        sa.Column('rounding_decimals', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'product_id', name='uq_valuation_company_product')
    )

    op.create_table(
        'inventory_reconciliations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('companies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('warehouse_id', sa.Uuid(), sa.ForeignKey('warehouses.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('product_id', sa.Uuid(), sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('ledger_balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('cached_stock_balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('discrepancy_delta', sa.Numeric(20, 6), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DETECTED'),
        sa.Column('before_balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('after_balance', sa.Numeric(20, 6), nullable=False),
        sa.Column('repair_reason', sa.String(length=255), nullable=True),
        sa.Column('evidence', sa.String(length=255), nullable=True),
        sa.Column('repaired_by', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('repaired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    if op.get_bind().dialect.name == "postgresql":
        for table in [
            'warehouse_locations', 'inventory_location_stocks', 'inventory_lots',
            'inventory_serials', 'inventory_stock_rules', 'inventory_alerts',
            'inventory_reservations', 'inventory_quarantines', 'physical_count_sessions',
            'physical_count_lines', 'inventory_picking_lists', 'inventory_picking_lines',
            'inventory_valuation_settings', 'inventory_reconciliations'
        ]:
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
            op.execute(f'CREATE POLICY {table}_tenant_policy ON "{table}" USING (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid) WITH CHECK (company_id = NULLIF(current_setting(\'app.current_company_id\', true), \'\')::uuid)')


def downgrade() -> None:
    for table in [
        'inventory_reconciliations', 'inventory_valuation_settings', 'inventory_picking_lines',
        'inventory_picking_lists', 'physical_count_lines', 'physical_count_sessions',
        'inventory_quarantines', 'inventory_reservations', 'inventory_alerts',
        'inventory_stock_rules', 'inventory_serials', 'inventory_lots',
        'inventory_location_stocks', 'warehouse_locations'
    ]:
        op.drop_table(table)
    op.drop_column('supply_lines', 'damaged_quantity')
