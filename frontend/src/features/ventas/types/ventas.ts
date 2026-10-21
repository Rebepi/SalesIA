export type DocumentStatus = "Borrador" | "Confirmada" | "Anulada";
export type PaymentStatus = "Sin cobrar" | "Parcial" | "Pagada" | "Vencida";
export type DeliveryStatus = "Pendiente" | "Parcial" | "Entregada" | "No aplica";
export type SunatStatus = "No aplica" | "Pendiente" | "Aceptado" | "Observado" | "Rechazado" | "Baja";
export type ReturnStatus = "Sin devolución" | "Parcial" | "Total";
export type VoucherType = "FACTURA" | "BOLETA" | "NOTA_CREDITO" | "NOTA_DEBITO" | "NOTA_VENTA";

export interface CreditNoteRecord {
  id: string;
  number: string;
  series: string;
  correlative: number;
  reason: string;
  reason_code: string;
  credit_note_type?: string;
  created_at: string;
  total_amount: number;
  sunat_status: SunatStatus;
  money_destination?: string;
  goods_destination?: string;
}

export interface DebitNoteRecord {
  id: string;
  number: string;
  series: string;
  correlative: number;
  reason: string;
  reason_code: string;
  reason_code_description?: string;
  date: string;
  created_at?: string;
  amount: number;
  total_amount?: number;
  tax_amount: number;
  sunat_status: SunatStatus;
  lines: Array<{
    concept: string;
    amount: number;
    tax_amount: number;
  }>;
}

export interface DispatchGuideRecord {
  id: string;
  guide_number: string;
  number?: string;
  series: string;
  transfer_reason: string;
  transfer_reason_description?: string;
  transport_mode: "PUBLIC" | "PRIVATE";
  transfer_date: string;
  gross_weight: number;
  total_weight_kg?: number;
  weight_unit: string;
  origin_address: string;
  destination_address: string;
  arrival_address?: string;
  vehicle_plate?: string;
  driver_name?: string;
  driver_document?: string;
  carrier_ruc?: string;
  carrier_name?: string;
  status: "Pendiente" | "En ruta" | "Entregada";
  sunat_status: SunatStatus;
  items: Array<{
    product_name: string;
    sku: string;
    quantity: number;
    unit_of_measure: string;
  }>;
}

export interface SaleRecord {
  zero_cost_lines_count?: number;
  id: string;
  sale_id: string;
  number: string;
  series: string;
  correlative: number;
  document_type: "INVOICE" | "RECEIPT" | "SALE_NOTE" | string;
  voucher_type?: VoucherType;
  created_at: string;
  confirmed_at?: string | null;
  due_date?: string | null;
  customer_id: string;
  customer_name: string;
  customer_document: string;
  customer_address?: string | null;
  sales_rep_id?: string | null;
  sales_rep_name?: string | null;
  branch_id: string;
  branch_name?: string | null;
  warehouse_id?: string | null;
  currency: string;
  exchange_rate: string | number;
  subtotal_amount?: string | number;
  tax_amount?: string | number;
  total_amount: string | number;
  paid_amount: string | number;
  balance_amount?: string | number;
  status: string;
  document_status: DocumentStatus;
  payment_status: PaymentStatus;
  delivery_status: DeliveryStatus;
  sunat_status: SunatStatus;
  return_status: ReturnStatus;
  is_credit: boolean;
  notes?: string | null;
  internal_observations?: string | null;
  delivery_address?: string | null;
  delivery_contact?: string | null;
  delivery_schedule?: string | null;
  coupon_code?: string | null;
  items_count?: number;
  origin?: "POS" | "Cotización" | "Pedido" | "Repetida";
  related_quotation_id?: string | null;
  related_order_id?: string | null;
  version?: number;
  sunat_error?: string | null;
  cancellation_reason?: string | null;
  related_credit_notes?: ReturnRecord[];
  related_debit_notes?: DebitNoteRecord[];
  dispatch_guides?: DispatchGuideRecord[];
}

export interface SaleKPIs {
  today_count: number;
  today_amount: number;
  month_count: number;
  month_amount: number;
  receivable_count: number;
  receivable_amount: number;
  overdue_count: number;
  overdue_amount: number;
  pending_delivery_count: number;
  sunat_rejected_count: number;
  old_drafts_count: number;
}

export interface VentasFilterState {
  only_zero_cost?: boolean;
  only_unassigned?: boolean;
  only_with_lines?: boolean;
  category?: string;
  date_basis?: "created" | "confirmed";
  dashboard_period?: string;
  dashboard_as_of?: string;
  search: string;
  date_shortcut: "all" | "today" | "yesterday" | "this_week" | "this_month" | "last_30_days" | "custom";
  date_from: string;
  date_to: string;
  customer_id: string;
  sales_rep_id: string;
  branch_id: string;
  warehouse_id: string;
  document_type: string;
  currency: string;
  document_status: string;
  payment_status: string;
  delivery_status: string;
  sunat_status: string;
  return_status: string;
  payment_method: string;
  min_amount: string;
  max_amount: string;
  only_with_balance: boolean;
  only_overdue: boolean;
  only_with_returns: boolean;
  origin: string;
}

export interface SavedView {
  id: string;
  name: string;
  filters: Partial<VentasFilterState>;
  columns?: string[];
}

export interface Installment {
  number: number;
  due_date: string;
  amount: number;
  paid_amount: number;
  status: "Pendiente" | "Pagada" | "Vencida";
}

export interface SaleLineDetail {
  id?: string;
  product_id: string;
  sku: string;
  name: string;
  product_name: string;
  quantity: number | string;
  delivered_quantity?: number | string;
  returned_quantity?: number | string;
  unit_price: number | string;
  unit_cost?: number | string;
  discount?: number | string;
  tax_amount?: number | string;
  total_amount: number | string;
  unit_of_measure?: string;
  notes?: string;
  serial_numbers?: string[];
  lot_number?: string;
  has_serials?: boolean;
  has_lots?: boolean;
}

export interface AppliedPayment {
  id: string;
  payment_id?: string;
  amount: number | string;
  currency: string;
  payment_method: string;
  status: string;
  reference_code?: string;
  cash_session_id?: string;
  cash_register_name?: string;
  user_email?: string;
  created_at: string;
  is_reversal?: boolean;
  reversed_payment_id?: string;
  reversal_reason?: string;
}

export interface DeliveryRecord {
  id: string;
  delivery_number: string;
  warehouse_name: string;
  address: string;
  status: "Pendiente" | "En ruta" | "Entregada";
  delivered_at?: string;
  recipient_name?: string;
}

export interface ReturnRecord {
  id: string;
  return_number: string;
  reason: string;
  date: string;
  total_refunded: number;
  goods_destination: "STOCK" | "MERMA" | "GARANTIA" | "CUARENTENA";
  money_destination: "EFECTIVO" | "MEDIO_ORIGINAL" | "SALDO_A_FAVOR" | "DESCUENTO_DEUDA";
  items: Array<{
    product_name: string;
    quantity: number;
    amount: number;
  }>;
}

export interface CommunicationLog {
  id: string;
  channel: "EMAIL" | "WHATSAPP";
  recipient: string;
  subject_or_template: string;
  sent_at: string;
  sent_by: string;
  status: "ENVIADO" | "FALLIDO" | "PENDIENTE";
}
