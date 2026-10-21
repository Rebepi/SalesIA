export interface ReceivableItem {
  sale_id: string;
  customer_id: string;
  customer_name?: string;
  currency?: string;
  branch_id?: string;
  series_number: string;
  total_amount: string;
  paid_amount: string;
  balance_due: string;
  due_date: string;
  aging_balances?: Record<string, string>;
  has_installments?: boolean;
  schedule_needs_review?: boolean;
  aging_bucket: "not_due" | "0-30" | "31-60" | "61-90" | "90+";
  status: string;
  created_at: string;
}

export interface CreditNoteItem {
  id: string;
  series: string;
  number: number;
  sale_id: string;
  total_amount: string;
  status: string;
  created_at: string;
}

export interface AccountsReceivableResponse {
  company_id: string;
  total_receivable: string | null;
  total_disputed: string | null;
  totals_by_currency: Record<string, { total_receivable: string; total_disputed: string; not_due: string }>;
  count: number;
  items: ReceivableItem[];
}

export interface AccountsReceivableTabProps {
  canWrite?: boolean;
}
