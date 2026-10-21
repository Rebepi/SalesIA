import { ReportScheduleConfig } from "../components/ReportScheduleBuilder";

export interface ReportTemplate {
  code: string;
  name: string;
  area: string;
  objective: string;
  required_permission: string;
  allowed_formats: string[];
  date_field: string;
  currency_support: string;
  status_filter_support: string[];
  schema_summary: {
    columns: string[];
    grain: string;
  };
}

export interface ReportRunItem {
  run_id: string;
  template_code: string;
  format: string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  progress_pct: number;
  row_count: number;
  file_size_kb: number;
  sha256_hash: string | null;
  cutoff_at: string;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
  error_message: string | null;
  parameters: Record<string, unknown>;
}

export interface ReportScheduleItem {
  version?: number;
  schedule_id: string;
  template_code: string;
  cron_expression: string;
  schedule?: ReportScheduleConfig;
  next_run_at?: string;
  error_message?: string;
  timezone: string;
  recipient_emails: string[];
  format: string;
  is_active: boolean;
  created_at: string;
  last_run_at: string | null;
  last_run_id: string | null;
  runs_count: number;
}

export interface ReportPreviewData {
  template_code: string;
  estimated_row_count: number;
  estimated_file_size_kb: number;
  columns: string[];
  sample_rows: Record<string, unknown>[];
  cutoff_at: string;
  authorized: boolean;
}

export interface ReportComparisonResult {
  report_a: { run_id: string; row_count: number; sha256_hash: string | null; cutoff_at: string };
  report_b: { run_id: string; row_count: number; sha256_hash: string | null; cutoff_at: string };
  identical_hash: boolean;
  rows_delta: number;
  cutoff_delta_seconds: number;
  same_cutoff_window: boolean;
}

export interface CorporateBranding {
  company_name: string;
  legal_name?: string;
  trade_name: string;
  tax_id: string;
  primary_color: string;
  secondary_color: string;
  footer_text: string;
  template_version: string;
}

export interface CollectionResponse<T> {
  items: T[];
  count: number;
}
