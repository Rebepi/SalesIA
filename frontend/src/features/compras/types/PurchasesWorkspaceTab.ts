export interface Supplier {
  id: string;
  tax_id: string;
  legal_name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  payment_terms_days: number;
  currency: string;
  bank_name: string | null;
  bank_account: string | null;
  notes: string | null;
  is_active: boolean;
}

export interface PurchaseOrder {
  id: string;
  document_number: string;
  supplier_id: string;
  warehouse_id: string;
  status: string;
  version: number;
  lines: {
    product_id: string;
    product_name?: string;
    quantity: string;
    processed_quantity: string;
    damaged_quantity: string;
    unit_cost: string;
    cancelled_quantity?: string;
    pending_quantity?: string;
  }[];
  details?: {
    total?: string;
    currency?: string;
    payment_terms_days?: number;
    delivery_date?: string;
    notes?: string;
  };
  created_at: string;
}

export interface PurchaseRequisition {
  id: string;
  version: number;
  details?: { suggested_supplier_id?: string; purchase_order_id?: string };
  document_number: string;
  warehouse_id: string;
  status: string;
  lines: {
    product_id: string;
    quantity: string;
    unit_cost: string;
  }[];
  created_at: string;
}

export interface ReplenishmentSuggestion {
  currency?: string;
  pending_purchase_quantity?: string;
  in_transit_quantity?: string;
  inventory_position?: string;
  warnings?: string[];
  purchase_commitments?: { order_id: string; quantity: string; delivery_date: string | null; overdue: boolean }[];
  product_id: string;
  product_name: string;
  sku: string;
  unit_cost: string;
  warehouse_id?: string;
  suggested_supplier_id?: string;
  current_available: string;
  assumptions: {
    daily_demand: string;
    lead_time_days: number;
    safety_stock: string;
    reorder_point: string;
  };
  suggested_quantity: string;
  data_insufficient: boolean;
  status: string;
  can_auto_approve: boolean;
}

export interface SupplierPerformance {
  supplier_id: string;
  legal_name: string;
  sample_size: number;
  weighted_score?: string | null;
  warning?: string | null;
  invoice_conformity_rate?: string | null;
  rejection_rate?: string | null;
  corrective_tasks?: { id: string; title: string; status: string; due_date: string | null; version: number; resolution_notes: string | null; can_edit: boolean }[];
  on_time_delivery_rate: string | null;
  fill_rate: string | null;
  quality_rate: string | null;
  sample_records: {
    receipt_id: string;
    purchase_order_id: string;
    product_id?: string;
    promised_date: string | null;
    actual_date: string;
    is_on_time: boolean | null;
    ordered_quantity: string;
    received_quantity: string;
    rejected_quantity: string;
  }[];
}

export interface ReceiptActionChoice {
  id: string;
  status: string;
  created_at: string;
  returnable_lines: { product_id: string; name: string; sku: string; quantity: string; returnable_quantity: string; unit_cost: string; lots: { lot_id: string; lot_code: string; quantity: string }[]; serial_numbers: string[] }[];
}

export interface ProcessTimeline {
  order_id: string;
  status: string;
  version: number;
  timeline: {
    stage: string;
    status: string;
    date?: string;
    version?: number;
    document_id?: string;
    invoice_number?: string;
  }[];
  line_balances: {
    product_id: string;
    ordered_quantity: string;
    received_quantity: string;
    pending_quantity: string;
    unit_cost: string;
  }[];
  next_recommended_step: string;
}
