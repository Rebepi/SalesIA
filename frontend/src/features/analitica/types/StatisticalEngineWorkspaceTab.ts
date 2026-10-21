export interface DatasetVariable {
  name?: string;
  label?: string;
  variable_name?: string;
  nature?: string;
  scale?: string;
}

export interface StatisticalDataset {
  id: string;
  name: string;
  active_version: number;
  row_count: number;
  variables?: DatasetVariable[];
}

export interface StatisticalCalculationResult {
  variable_name: string;
  n: number;
  excluded_count: number;
  mean: string;
  median: string;
  variance: string;
  stdev: string;
  skewness: string;
  min: string;
  max: string;
  precision: number;
  algorithm: string;
  algorithm_version: string;
  symmetry_diagnosis: string;
  explanation: string;
  dataset_id: string;
  dataset_version: number;
}

export interface StatisticalEngineWorkspaceTabProps {
  canWrite?: boolean;
}
