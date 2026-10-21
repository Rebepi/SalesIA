import { DocumentStatus, PaymentStatus, DeliveryStatus, SunatStatus, ReturnStatus, Installment, DeliveryRecord, ReturnRecord, CommunicationLog, VoucherType, CreditNoteRecord, DebitNoteRecord, DispatchGuideRecord } from "./ventas";

export interface SaleDetailLine {
  id?: string;
  product_id: string;
  sku: string;
  product_name: string;
  name?: string;
  quantity: number | string;
  delivered_quantity?: number | string;
  returned_quantity?: number | string;
  unit_price: number | string;
  unit_cost?: number | string;
  discount?: number | string;
  tax_rate?: number | string;
  tax_amount?: number | string;
  subtotal?: number | string;
  total_amount?: number | string;
  unit_of_measure?: string;
}

export interface SaleDetailPayment {
  id: string;
  amount: string | number;
  currency?: string;
  payment_method: string;
  reference_code?: string;
  cash_session_id?: string;
  cash_register_name?: string;
  user_email?: string;
  created_at: string;
  is_reversal?: boolean;
  reversed_payment_id?: string;
  reversal_reason?: string;
}

export interface SaleCommissionInfo {
  sales_rep_id?: string;
  sales_rep_name?: string;
  commission_rate: number;
  commission_amount: number;
  status: "Pendiente" | "Liquidada" | "Anulada";
}

export interface SaleAuditEntry {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  previous_value?: string;
  new_value?: string;
  details?: string;
}

export interface SaleDetailData {
  id: string;
  sale_id?: string;
  number?: string;
  series?: string;
  correlative?: number;
  document_type?: "INVOICE" | "RECEIPT" | "SALE_NOTE" | string;
  voucher_type?: VoucherType;
  status: "draft" | "confirmed" | "paid" | "cancelled" | string;
  document_status?: DocumentStatus;
  payment_status?: PaymentStatus;
  delivery_status?: DeliveryStatus;
  sunat_status?: SunatStatus;
  return_status?: ReturnStatus;
  currency: string;
  exchange_rate?: string | number;
  subtotal_amount?: string | number;
  tax_amount?: string | number;
  total_amount: string | number;
  paid_amount: string | number;
  balance_amount?: string | number;
  customer_id?: string;
  customer_name?: string;
  customer_document?: string;
  sales_rep_id?: string;
  sales_rep_name?: string;
  branch_id?: string;
  branch_name?: string;
  warehouse_id?: string;
  created_at?: string;
  confirmed_at?: string | null;
  sunat_sent_at?: string | null;
  delivered_at?: string | null;
  due_date?: string | null;
  due_at?: string | null;
  payment_terms_days?: number;
  due_calendar?: { payment_terms_days: number; legacy_elapsed_days?: boolean; basis?: string; roll?: string; before_roll?: string; calendar: { timezone: string; version: number; company_version: number } } | null;
  is_credit?: boolean;
  notes?: string | null;
  internal_observations?: string | null;
  related_quotation_id?: string | null;
  related_order_id?: string | null;
  lines?: SaleDetailLine[];
  payments?: SaleDetailPayment[];
  installments?: Installment[];
  deliveries?: DeliveryRecord[];
  returns?: ReturnRecord[];
  credit_notes?: CreditNoteRecord[];
  debit_notes?: DebitNoteRecord[];
  dispatch_guides?: DispatchGuideRecord[];
  xml_url?: string;
  pdf_url?: string;
  cdr_url?: string;
  sunat_response_message?: string;
  sunat_hash?: string;
  communications?: CommunicationLog[];
  commission?: SaleCommissionInfo;
  audit_trail?: SaleAuditEntry[];
}

export interface SaleDetailModalProps {
  sale: SaleDetailData | null;
  canWrite?: boolean;
  canViewCosts?: boolean;
  onClose: () => void;
  onConfirmSale?: (saleId: string) => void;
  onOpenPayment?: (sale: SaleDetailData) => void;
  onOpenReturn?: (sale: SaleDetailData) => void;
  onCancelSale?: (saleId: string) => void;
  onDuplicateSale?: (sale: SaleDetailData) => void;
  onOpenCommunication?: (sale: SaleDetailData) => void;
}
