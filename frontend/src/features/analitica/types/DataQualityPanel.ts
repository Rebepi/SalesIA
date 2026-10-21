export interface QualityReport {
  received: number;
  used: number;
  excluded: number;
  completeness_pct: number;
  excluded_by_reason: Record<string, number>;
  null_counts: Record<string, number>;
  variable_completeness: Record<string, number>;
  error_rates: Record<string, number>;
  imputation_warnings: string[];
}

export interface DatasetVersionItem {
  version: number;
  created_at: string;
  row_count: number;
  sha256_hash: string;
  completeness_pct: number;
  status: string;
}

export interface DatasetVersionDetail {
  dataset_id: string;
  version: number;
  grain: string;
  status: string;
  row_count: number;
  sha256_hash: string;
  created_at: string;
  quality_report: QualityReport;
  sample: Record<string, unknown>[];
  variables: Record<string, unknown>[];
  created_by?: string;
}

export interface DatasetItem {
  id: string;
  name: string;
  grain: string;
  source_entity: string;
  active_version: number;
  row_count: number;
  created_at: string;
}

export interface DataQualityPanelProps {
  datasetId?: string;
  onVersionCreated?: (newVersion: number) => void;
  canCalculate?: boolean;
}
