export interface RefundItem {
  id: string;
  payment_id: string;
  amount: string;
  currency: string;
  reason: string;
  status: "solicitado" | "aprobado" | "enviado" | "pendiente" | "confirmado" | "fallido" | "requiere_conciliacion" | string;
  provider_reference: string | null;
  failure_reason: string | null;
  return_id: string | null;
  created_at: string;
}

export type RefundSection = "refunds" | "settlements" | "credit" | "policy";

export interface RefundsWorkspaceTabProps {
  section?: RefundSection;
  onNavigate?: (section: RefundSection) => void;
  canWrite?: boolean;
}

export interface PaymentChoice extends Record<string, unknown> {
  id: string;
  sale_number: string;
  customer_name: string;
  customer_document: string;
  amount: string;
  currency: string;
  payment_method: string;
  reference_code?: string | null;
}


export interface RefundPaymentDetails {
  refunded_amount: string;
  refundable_amount: string;
  refunds: { refund_id: string; amount: string; reason: string; status: string; created_at: string }[];
  options: {
    currency: string;
    payment_method: string;
    available_amount: string;
    reversed_amount: string;
    requires_return: boolean;
    returns: { id: string; created_at: string; currency: string; available_amount: string; retained_total: string; applied_amount: string; warnings: string[] }[];
    cash_sessions: { id: string; terminal_code: string; balance: string }[];
  };
}
