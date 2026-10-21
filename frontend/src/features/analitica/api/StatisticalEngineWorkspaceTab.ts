import { apiClient } from "../../../api/client";
import { StatisticalDataset } from "../types/StatisticalEngineWorkspaceTab";
import { StatisticalCalculationResult } from "../types/StatisticalEngineWorkspaceTab";

export function solicitarLoadDatasets() {
  return apiClient.request<{ items: StatisticalDataset[] }>("/api/v1/datasets");
}

export function solicitarDatos({ selectedDataset }: { selectedDataset: StatisticalDataset }) {
  return apiClient.request<{ sample?: Record<string, unknown>[]; preview_sample?: Record<string, unknown>[] }>(`/api/v1/datasets/${selectedDataset.id}/versions/${selectedDataset.active_version}`);
}

export function solicitarHandleExecute({ selectedDataset, selectedVariable, nullPolicy, precision }: { selectedDataset: StatisticalDataset; selectedVariable: string; nullPolicy: string; precision: number }) {
  return apiClient.request<StatisticalCalculationResult>("/api/v1/statistics/descriptive-summary", {
    method: "POST",
    body: JSON.stringify({
      dataset_id: selectedDataset.id,
      dataset_version: selectedDataset.active_version,
      variable_name: selectedVariable,
      null_policy: nullPolicy,
      precision
    })
  });
}
