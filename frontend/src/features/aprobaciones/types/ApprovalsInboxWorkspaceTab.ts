export interface ApprovalRequestItem {
  id: string;
  code: string;
  requester_name: string;
  requester_email: string;
  operation_type: string;
  impact_summary: string;
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  evidence: string;
  document_id: string;
  document_version: number;
  server_document_version: number;
  status: "pending" | "approved" | "rejected" | "stale";
  document_changed?: boolean;
  stage_index?: number;
  stage_name?: string;
  stage_count?: number;
  due_at?: string | null;
  created_at: string;
}

export interface ApprovalApiItem {
  id: string;
  code: string;
  requester_name: string;
  requester_email: string;
  resource_type: string;
  resource_id: string;
  document_version: number;
  policy_name: string;
  evidence: string;
  status: "pending" | "approved" | "rejected" | "stale";
  server_document_version?: number;
  document_changed?: boolean;
  stage_index?: number;
  stage_name?: string;
  stage_count?: number;
  due_at?: string | null;
  created_at: string;
}

export interface ApprovalsInboxWorkspaceTabProps {
  canWrite?: boolean;
}
