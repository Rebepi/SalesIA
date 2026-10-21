import { apiClient } from "../../../api/client";
import { AnalyticsExecutionRun } from "../types/AnalyticsHistoryWorkspaceTab";
import { AnalysisApiRecord } from "../types/AnalyticsHistoryWorkspaceTab";

export function solicitarHandleRepeatRun({ original }: { original: AnalyticsExecutionRun }) {
  return apiClient.request<AnalysisApiRecord>(`/api/v1/analyses/${original.id}/repeat`, { method: "POST", body: JSON.stringify({ new_version: original.dataset_version }) });
}
