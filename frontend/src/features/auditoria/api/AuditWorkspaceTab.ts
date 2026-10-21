import { apiClient } from "../../../api/client";

export function solicitarHandleVerifyIntegrity() {
  return apiClient.request<{ is_valid: boolean; verified_count: number; legacy_unsealed_count?: number; broken_at_id?: string; reason?: string }>("/api/v1/audit/logs/verify");
}

export function solicitarHandleExport() {
  return apiClient.request<{ cryptographic_seal: string; exported_at: string; data: unknown[] }>("/api/v1/audit/logs/export", { method: "POST" });
}
