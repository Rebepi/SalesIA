export interface CashMovement {
  movement_id: string;
  movement_type: "DEPOSIT" | "WITHDRAWAL";
  amount: string;
  reason: string;
  balance_after: string;
  timestamp: string;
  actor_id: string;
}

export interface CashSession {
  id: string;
  session_id: string;
  branch_id: string;
  user_id: string;
  terminal_code: string;
  currency: string;
  status: "open" | "closed";
  opened_at: string;
  closed_at: string | null;
  initial_cash: string;
  expected_cash: string;
  actual_cash: string | null;
  difference_cash: string | null;
  notes: string | null;
  movements: CashMovement[];
  can_count: boolean;
  can_approve: boolean;
  control: {
    version?: number;
    is_current?: boolean;
    approval_status?: "pending" | "approved" | "rejected" | "not_required";
    counted_at?: string;
    counted_cash?: string;
    denominations?: Record<string, number>;
    non_cash_totals?: Record<string, string>;
    history?: { version: number; counted_at: string; counted_cash: string; approval_status: string }[];
    approval_history?: { approved: boolean; reviewed_at: string; notes: string }[];
  };
}

export type CashSection = "sessions" | "movements" | "counts" | "custody" | "petty" | "forecast";

export interface CashRegisterWorkspaceTabProps {
  section?: CashSection;
  canWrite?: boolean;
  currentBranchId?: string;
}
