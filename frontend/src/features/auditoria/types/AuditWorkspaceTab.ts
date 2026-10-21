export interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  trace_id: string;
  ip_address?: string;
  payload_diff: Record<string, unknown>;
  chain_hash?: string;
  created_at: string;
}

export interface AuditWorkspaceTabProps {
  canWrite?: boolean;
}
