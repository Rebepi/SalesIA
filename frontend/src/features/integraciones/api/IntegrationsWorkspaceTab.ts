import { apiClient } from "../../../api/client";
import { IntegrationConnector } from "../types/IntegrationsWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ items: IntegrationConnector[] }>("/api/v1/integrations");
}

export function solicitarHandleCreate({ provider, category, mode, credential }: { provider: string; category: string; mode: "test" | "live"; credential: string }) {
  return apiClient.request("/api/v1/integrations", { method: "POST", body: JSON.stringify({ provider, category, mode, credential }) });
}

export function solicitarHandleRotateCredential({ connectorId, credential }: { connectorId: string; credential: string }) {
  return apiClient.request(`/api/v1/integrations/${connectorId}/credential`, { method: "PATCH", body: JSON.stringify({ credential }) });
}

export function solicitarHandleToggleMode({ connector, mode }: { connector: IntegrationConnector; mode: string }) {
  return apiClient.request(`/api/v1/integrations/${connector.id}/mode`, { method: "PATCH", body: JSON.stringify({ mode }) });
}

export function solicitarHandleTestConnection({ connector }: { connector: IntegrationConnector }) {
  return apiClient.request<{ status: IntegrationConnector["status"]; latency_ms: number; checked_at: string }>(`/api/v1/integrations/${connector.id}/diagnose`, { method: "POST" });
}
