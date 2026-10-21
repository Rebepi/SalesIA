export interface SystemServiceStatus {
  name: string;
  status: "healthy" | "degraded" | "down";
  latency_ms: number;
  version: string;
  uptime_pct: string;
  details: string;
}

export interface FailedJobItem {
  id: string;
  task_name: string;
  trace_id: string;
  error_message: string;
  retry_count: number;
  created_at: string;
  status: "failed" | "retrying" | "resolved";
}

export interface SystemHealthSupportWorkspaceTabProps {
  canWrite?: boolean;
  isTechAdmin?: boolean;
}
