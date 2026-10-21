import { apiClient } from "../../../api/client";
import type { Row } from "../types/clientes";

export function listarClientes(page: number, pageSize: number, search: string, signal: AbortSignal) {
  return apiClient.request<Row[] | { items: Row[]; total_count?: number; count?: number }>(
    `/api/v1/customers?limit=${pageSize}&offset=${page * pageSize}&search=${encodeURIComponent(search)}`,
    { signal }
  );
}

export function exportarClientes() {
  return apiClient.request<{ format: string; count: number; data: unknown }>("/api/v1/customers/export", {
    method: "POST",
    body: JSON.stringify({ reason: "Exportación de cartera CRM", format: "csv" })
  });
}
