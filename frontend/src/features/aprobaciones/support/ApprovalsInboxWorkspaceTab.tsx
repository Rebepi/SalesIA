import { ApprovalRequestItem } from "../types/ApprovalsInboxWorkspaceTab";
import { ApprovalApiItem } from "../types/ApprovalsInboxWorkspaceTab";

export function toApprovalItem(item: ApprovalApiItem): ApprovalRequestItem {
  return {
    id: item.id,
    code: item.code,
    requester_name: item.requester_name,
    requester_email: item.requester_email,
    operation_type: item.policy_name,
    impact_summary: `${item.resource_type} ${item.resource_id}`,
    risk_level: "MEDIUM",
    evidence: item.evidence || "Sin evidencia adicional registrada.",
    document_id: item.resource_id,
    document_version: item.document_version,
    server_document_version: item.server_document_version ?? item.document_version,
    document_changed: item.document_changed,
    stage_index: item.stage_index,
    stage_name: item.stage_name,
    stage_count: item.stage_count,
    due_at: item.due_at,
    status: item.status,
    created_at: item.created_at
  };
}
