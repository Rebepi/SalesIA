export interface RowErrorItem {
  row_number: number;
  field: string;
  rejected_value: string;
  reason: string;
}

export interface ImportJobResult {
  attachment_id?: string;
  column_mapping?: Record<string, string>;
  corrections?: Record<string, Record<string, string>>;
  detected?: { delimiter: string; encoding: string; source_columns: string[] };
  rejected_rows?: Array<{ row_number: number; values: Record<string, string> }>;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  row_errors: Array<{ row: number; column: string; error: string }>;
  is_duplicate_file: boolean;
  preview: Array<Record<string, string>>;
  imported?: number;
  processed_rows?: number;
}

export interface ImportJobResponse {
  job_id: string;
  status: string;
  progress_pct: number;
  result: ImportJobResult | null;
}

export interface ImportHistoryItem extends ImportJobResponse { target_entity: "customers" | "products" | "inventory_adjustments"; created_at: string }

export interface Inspection { columns: string[]; delimiter: string; encoding: string; total_rows: number }

export interface ImportsWorkspaceTabProps {
  canWrite?: boolean;
  permissions?: string[];
}
