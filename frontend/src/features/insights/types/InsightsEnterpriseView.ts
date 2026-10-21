export interface InsightActionDraft {
  action_id: string;
  action_type: string;
  title: string;
  description: string;
  projected_impact: string;
  requires_manual_confirmation: boolean;
  financial_auto_execution: boolean;
  draft_preview?: Record<string, any>;
}

export interface InsightEvidenceData {
  metric_name: string;
  current_value: string;
  baseline_value: string;
  numerator?: string;
  denominator?: string;
  difference_pct?: string;
  threshold?: string;
  sample_size?: number;
  cutoff_date?: string;
  filters_applied?: Record<string, any>;
}

export interface InsightItem {
  id: string;
  title: string;
  cifra_clave: string;
  period: string;
  severity: "critical" | "high" | "medium" | "low" | string;
  status: "new" | "pending" | "read" | "in_review" | "acknowledged" | "resolved" | "dismissed" | string;
  detected_at?: string;
  observation?: string;
  interpretation?: string;
  suggested_action?: string;
  evidence?: string;
  evidence_data?: InsightEvidenceData;
  suggested_actions?: InsightActionDraft[];
  cost_confidential?: boolean;
  snoozed_until?: string;
  task_id?: string;
}

export interface InsightsEnterpriseViewProps {
  insights?: InsightItem[];
  onStatusChange?: (id: string, newStatus: string, reason?: string) => Promise<void> | void;
  onBulkRead?: () => Promise<void> | void;
  onFeedback?: (id: string, helpful: boolean, comment?: string) => Promise<void> | void;
}
