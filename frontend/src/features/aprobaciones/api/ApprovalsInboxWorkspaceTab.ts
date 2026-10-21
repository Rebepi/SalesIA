import { apiClient } from "../../../api/client";
import { ApprovalRequestItem } from "../types/ApprovalsInboxWorkspaceTab";
import { ApprovalApiItem } from "../types/ApprovalsInboxWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ items: ApprovalApiItem[] }>("/api/v1/collaboration/approvals");
}

export function solicitarHandleApprove({ item }: { item: ApprovalRequestItem }) {
  return apiClient.request<{ status: "pending" | "approved" | "rejected" }>(`/api/v1/collaboration/approvals/${item.id}/decide`, { method: "POST", body: JSON.stringify({ decision: "approved", reason: "Aprobación confirmada desde la bandeja", current_document_version: item.server_document_version }) });
}

export function solicitarHandleConfirmReject({ rejectionModalItem, rejectionReason }: { rejectionModalItem: ApprovalRequestItem; rejectionReason: string }) {
  return apiClient.request(`/api/v1/collaboration/approvals/${rejectionModalItem.id}/decide`, { method: "POST", body: JSON.stringify({ decision: "rejected", reason: rejectionReason.trim(), current_document_version: rejectionModalItem.server_document_version }) });
}
