export interface CustomerData {
  id?: string;
  code: string;
  legal_name: string;
  doc_type: string;
  doc_number: string;
  email?: string;
  phone?: string;
  credit_limit?: string;
  is_active?: boolean;
}

export interface CustomerEditorDrawerProps {
  isOpen: boolean;
  initialData?: CustomerData | null;
  onClose: () => void;
  onSaved: (customer: CustomerData) => void;
  quickMode?: boolean;
}

export type Row = Record<string, string | number | boolean | null>;

export interface FichaClienteProps {
  customerId: string;
  customerName: string;
  canWrite: boolean;
  allCustomers: Row[];
  onClose: () => void;
  onRefresh: () => void;
  onAction?: (action: "quotation" | "order" | "sale" | "payment" | "repeat", resourceId?: string) => void;
}

export type FichaClienteTab = "overview" | "contacts" | "addresses" | "terms" | "history" | "notes" | "merge";

export interface CustomerAnalyticsItem {
  customer_id: string;
  code: string;
  legal_name: string;
  customer_type: "new" | "recurring" | "inactive" | "prospect" | "final_consumer";
  orders_count: number;
  total_revenue: string;
  recency_days: number | null;
  average_ticket: string | null;
  revenue_share_pct: string;
}

export interface CustomerAnalyticsSummary {
  total_customers: number;
  active_in_period: number;
  total_revenue: string;
  new_customers_count: number;
  recurring_customers_count: number;
  inactive_customers_count: number;
  top_20_concentration_pct: string;
}

export interface CustomerCohortItem {
  cohort: string;
  size: number;
  retention_pct: (string | null)[];
}

export interface CustomerAnalyticsTabProps {
  canWrite?: boolean;
}
