export type Submodule = "stock" | "kardex" | "purchases" | "shipping" | "transfers" | "counts" | "lots_serials" | "locations_rules" | "alerts_reconcile";

export interface Warehouse {
  warehouse_id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  unit_price: number;
  unit_cost?: string;
  barcode?: string;
}

export interface StockItem {
  id: string;
  warehouse_id: string;
  product_id: string;
  sku: string;
  product_name: string;
  unit_of_measure: string;
  physical_quantity: string;
  reserved_quantity: string;
  available_quantity: string;
  transit_quantity: string;
  quarantine_quantity: string;
  blocked_quantity: string;
  average_cost: string;
  updated_at: string;
}

export interface KardexItem {
  id: string;
  warehouse_id: string;
  product_id: string;
  movement_type: string;
  reference_doc_type: string;
  reference_doc_id: string;
  quantity_delta: string;
  resulting_physical_qty: string;
  unit_cost: string;
  moving_average_cost: string;
  occurred_at: string;
}

export interface TransferItem {
  id: string;
  document_number: string;
  source_warehouse_id: string;
  destination_warehouse_id: string;
  status: string;
  lines: {
    product_id: string;
    product_name?: string;
    quantity: string;
    processed_quantity: string;
    damaged_quantity: string;
    unit_cost: string;
  }[];
  created_at: string;
}

export interface CountItem {
  id: string;
  count_code?: string;
  version?: number;
  warehouse_id: string;
  status: string;
  notes: string | null;
  cutoff_at: string;
  created_at: string;
  lines: {
    id: string;
    product_id: string;
    counted_quantity: string | null;
    counted_at?: string | null;
    snapshot_system_quantity: string | null;
    discrepancy_quantity: string | null;
  }[];
}

export interface LotItem {
  id: string;
  product_id: string;
  lot_code: string;
  expiration_date: string | null;
  is_blocked: boolean;
}

export interface SerialItem {
  id: string;
  warehouse_id: string;
  product_id: string;
  serial_number: string;
  status: string;
}

export interface LocationItem {
  id: string;
  warehouse_id: string;
  aisle: string;
  rack: string;
  shelf: string;
  bin: string;
  code: string;
  capacity_units: string;
  is_active: boolean;
}

export interface RuleItem {
  id: string;
  warehouse_id: string;
  product_id: string;
  min_quantity: string;
  max_quantity: string;
  reorder_point: string;
  reorder_quantity: string;
  is_active?: boolean;
}

export interface AlertItem {
  id: string;
  warehouse_id: string;
  product_id: string | null;
  alert_type: string;
  severity: string;
  message: string;
  computed_at: string;
}

export interface QuarantineItem {
  id: string;
  warehouse_id: string;
  product_id: string;
  quantity: string;
  reason: string;
  status: string;
}
