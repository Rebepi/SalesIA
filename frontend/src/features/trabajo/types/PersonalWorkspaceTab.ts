export interface PersonalWorkspaceTabProps {
  branchId?: string;
  branches?: Array<{ branch_id?: string; name?: string; code?: string; timezone?: string }>;
  baseCurrency?: string;
  onNavigate?: (view: string, itemId?: string) => void;
  onOpenOrder?: (orderId: string) => void;
  onOpenCustomer?: (customerId: string) => void;
  onOpenResource?: (type: string, id: string) => void;
}

export interface PersonalTask {
  id: string;
  title: string;
  description?: string | null;
  due_date: string | null;
  priority: "high" | "normal" | "low" | "urgent";
  status: "pending" | "in_progress" | "completed" | "cancelled";
  creator_id?: string;
  assignee_id?: string;
  resource_type?: string | null;
  resource_id?: string | null;
  resource_name?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AssignedOrder {
  order_id: string;
  order_number: string;
  customer_id: string;
  customer_name?: string;
  total_amount: string | number;
  currency?: string;
  status: string;
  created_at: string;
}

export interface AssignedCustomer {
  id: string;
  code: string;
  legal_name: string;
  doc_number: string;
  current_balance: string | number | null;
  assigned_sales_rep_id?: string | null;
}

export interface SalesProgressData {
  isRepresentative: boolean;
  hasQuota: boolean;
  currentSales: number;
  grossSales: number;
  refunds: number;
  netSales: number;
  quota: number;
  attainment: number | null;
  gap: number;
}
