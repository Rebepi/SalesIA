export interface OrderLine {
  product_id: string;
  sku: string;
  product_name?: string;
  name?: string;
  quantity: string;
  unit_price: string;
  reserved_quantity?: string;
  fulfilled_quantity?: string;
  cancelled_quantity?: string;
}

export interface OrderItem {
  id?: string;
  order_id?: string;
  order_number: string;
  customer_id: string;
  customer_name?: string;
  status: "draft" | "pending_approval" | "confirmed" | "backorder" | "partially_fulfilled" | "fulfilled" | "cancelled";
  currency: string;
  total_amount: string;
  stock_reserved: boolean;
  reservation_expires_at?: string;
  delivery_terms?: string;
  lines?: OrderLine[];
  created_at: string;
  branch_id?: string;
  warehouse_id?: string;
  payment_terms_days?: number;
  customer_po_number?: string;
  history?: Array<{ status: string; timestamp: string; actor?: string; note?: string }>;
  picking?: { status?: string; lines?: Array<{ order_line_number?: number; product_id: string; sku: string; name: string; expected_quantity: string; picked_quantity: string; verified: boolean }> };
}

export interface CustomerChoice extends Record<string, unknown> { id: string; legal_name: string; doc_number?: string; code?: string }

export interface ProductChoice extends Record<string, unknown> { id: string; name: string; sku: string; unit_price?: string }

export interface BranchChoice { id?: string; branch_id?: string; name: string; code?: string }

export interface WarehouseChoice { id?: string; warehouse_id?: string; branch_id?: string; name: string; code?: string }

export interface DraftLine { product_id: string; product?: ProductChoice; quantity: string; discount_pct: string }
