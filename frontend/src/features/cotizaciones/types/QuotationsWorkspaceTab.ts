export interface QuotationItem {
  id?: string;
  quotation_id?: string;
  quotation_number: string;
  customer_id: string;
  customer_name?: string;
  branch_id?: string | null;
  version: number;
  status: "draft" | "pending" | "accepted" | "converted" | "rejected" | "superseded";
  currency: string;
  subtotal_amount: string;
  tax_amount: string;
  total_amount: string;
  valid_until?: string;
  created_at: string;
  lines?: Array<{ product_id: string; sku?: string; name?: string; quantity: string; discount_pct: string }>;
  payment_terms_days?: number;
  delivery_terms?: string;
  notes?: string;
  special_conditions?: string;
  seller_id?: string;
  sent_at?: string;
  opened_at?: string;
  accepted_at?: string;
}

export interface CustomerItem extends Record<string, unknown> {
  id: string;
  customer_id?: string;
  code: string;
  legal_name: string;
  doc_type: string;
  doc_number: string;
}

export interface ProductItem extends Record<string, unknown> {
  id: string;
  product_id?: string;
  sku: string;
  name: string;
  unit_price: string;
  unit_of_measure?: string;
}

export interface QuotationLine {
  product_id: string;
  quantity: string;
  discount_pct: string;
  product?: ProductItem;
}

export interface QuotationDraft {
  customer?: CustomerItem;
  branchId: string;
  validDays: string;
  lines: QuotationLine[];
  paymentTerms: string;
  deliveryTerms: string;
  notes: string;
  specialConditions: string;
  sellerId: string;
}
