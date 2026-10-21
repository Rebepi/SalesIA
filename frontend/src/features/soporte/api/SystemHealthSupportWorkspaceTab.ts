import { apiClient } from "../../../api/client";

export function solicitarLoad() {
  return apiClient.request<{ status: string; app: string; version: string; environment: string }>("/api/v1/health/live");
}

export function solicitarLoad2() {
  return apiClient.request<{ status: string; database: string }>("/api/v1/health/ready");
}

export function solicitarLoad3() {
  return apiClient.request<{ status: string; pending_jobs: number; failed_jobs: number; outbox_backlog: number }>("/api/v1/operations/system-status");
}

export function solicitarLoad4() {
  return apiClient.request<{ slo_targets: { availability_target: number } }>("/api/v1/operations/metrics");
}

export function solicitarHandleRetryJob({ jobId }: { jobId: string }) {
  return apiClient.request(`/api/v1/operations/jobs/${jobId}/retry`, { method: "POST" });
}
