export interface AnalyticsExecutionRun {
  id: string;
  code: string;
  analyst_email: string;
  analysis_type: string;
  dataset_name: string;
  dataset_version: number;
  parameters: Record<string, unknown>;
  status: "completed" | "processing" | "failed" | "cancelled";
  result_summary: string;
  algorithm_version: string;
  created_at: string;
  is_reproducible: boolean;
  repeat_unavailable_reason: string;
  result: Record<string, unknown> | null;
  explanation?: string;
  dataset_id: string | null;
  variable_name?: string;
}

export interface AnalysisApiRecord {
  id: string;
  name: string;
  dataset_id: string | null;
  dataset_name?: string;
  created_by_name?: string;
  explanation?: string;
  dataset_version: number;
  variable_name?: string;
  analysis_type: string;
  result: Record<string, unknown> | null;
  transformations_applied?: unknown[];
  algorithm_version: string;
  created_by: string;
  created_at: string;
  status: "completed" | "processing" | "failed" | "cancelled";
}

export interface AnalyticsHistoryWorkspaceTabProps {
  canWrite?: boolean;
}
