import { apiClient } from "../../../api/client";
import { InsightActionDraft } from "../types/InsightsEnterpriseView";
import { InsightItem } from "../types/InsightsEnterpriseView";

export function solicitarDatos() {
  return apiClient.request<{ items: InsightItem[] }>("/api/v1/insights?limit=100");
}

export function solicitarHandleBulkReadClick() {
  return apiClient.request<{ marked_read_count: number }>("/api/v1/insights/bulk-read", { method: "POST" });
}

export function solicitarSubmitFeedback({ insightId, helpful, feedbackComment }: { insightId: string; helpful: boolean; feedbackComment: string }) {
  return apiClient.request(`/api/v1/insights/${insightId}/feedback`, { method: "POST", body: JSON.stringify({ helpful, comment: feedbackComment }) });
}

export function solicitarChangeStatus({ insightId, status, reason }: { insightId: string; status: string; reason: string }) {
  return apiClient.request(`/api/v1/insights/${insightId}/status`, { method: "PATCH", body: JSON.stringify({ status, reason }) });
}

export function solicitarPrepareAction({ activeActionModal }: { activeActionModal: { insight: InsightItem; action: InsightActionDraft; } }) {
  return apiClient.request(`/api/v1/insights/${activeActionModal.insight.id}/actions/${activeActionModal.action.action_id}/prepare`, { method: "POST" });
}
