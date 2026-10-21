export interface CustomerItem extends Record<string, unknown> {
  id: string;
  customer_id?: string;
  code: string;
  legal_name: string;
  doc_type: string;
  doc_number: string;
  email?: string;
  phone?: string;
  credit_limit?: string | null;
  current_balance?: string | null;
  payment_terms_days?: number;
  preferred_currency?: string;
  price_list_id?: string | null;
  is_credit_blocked?: boolean;
  credit_block_reason?: string | null;
  is_walk_in?: boolean;
  address?: string | null;
}

export interface ProductItem extends Record<string, unknown> {
  id: string;
  product_id?: string;
  sku: string;
  name: string;
  unit_price: string;
  tax_rate: string;
  unit_of_measure: string;
  available_quantity: string;
  physical_quantity: string;
  reserved_quantity: string;
  track_inventory: boolean;
  has_lots: boolean;
  has_serials: boolean;
  next_restock_at?: string | null;
  category_name?: string;
  brand_name?: string;
  barcode?: string;
  other_warehouse_stock?: Record<string, number>;
}

export interface SaleCartLine {
  product: ProductItem;
  quantity: number;
  unit_price?: number;
  discount?: number;
  note?: string;
  is_free_concept?: boolean;
  serialNumbers?: string[];
}

export interface SerialItem {
  id: string;
  serial_number: string;
  status: string;
}

export interface WarehouseItem {
  warehouse_id: string;
  code: string;
  name: string;
  branch_id: string;
  is_active: boolean;
}

export interface BranchItem {
  branch_id: string;
  name: string;
  timezone: string;
  code?: string;
}

export interface PosDraft {
  customer?: CustomerItem;
  warehouseId: string;
  isCredit: boolean;
  documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE";
  cart: SaleCartLine[];
  couponCode?: string;
  notes?: string;
  deliveryAddress?: string;
  internalObservations?: string;
  exchangeRate?: string;
  salesRepId?: string;
}

export interface PricingResult {
  product_id: string;
  final_unit_price: string;
  subtotal: string;
  tax_amount: string;
  total_estimated: string;
  discount_applied: string;
  rules_applied: { rule_type: string; name?: string; code?: string; discount_percentage?: string; discount_amount?: string; fixed_price?: string }[];
}

export interface SalesRepItem {
  id: string;
  full_name: string;
  code: string;
}

export interface NewSalePOSModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaleCreated: (saleId: string, isDraft?: boolean) => void;
  initialCustomerId?: string;
  sourceSaleId?: string;
}