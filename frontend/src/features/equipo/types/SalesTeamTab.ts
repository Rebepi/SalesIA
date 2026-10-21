export type Row = Record<string, string | number | boolean | null>;

export interface SalesRepItem {
  rep_id: string;
  code: string;
  user_id: string | null;
  full_name: string;
  branch_id: string | null;
  team: string | null;
  supervisor_id: string | null;
  territory: string;
  monthly_quota: string | null;
  current_sales: string;
  total_sales: string;
  sales_count: number;
  ticket_average: string;
  average_ticket: string;
  returns_amount: string;
  active_days: number;
  target_quota: string | null;
  quota_attainment_pct: string | null;
  target_configured: boolean;
  is_active: boolean;
}
