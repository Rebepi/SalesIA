import { selectorSeed } from "../../../api/selectorSeed";
import { apiClient, SearchResultItem } from "../../../api/client";
import { SaleDetailData } from "../../../features/ventas/components/SaleDetailModal";
import { Row } from "../types/OperationsWorkspace";

export function solicitarOpenSearchEntity({ item }: { item: SearchResultItem }) {
  return apiClient.request<Row>(`/api/v1/customers/${encodeURIComponent(item.id)}`);
}

export function solicitarOpenSearchEntity2({ item }: { item: SearchResultItem }) {
  return apiClient.request<Row>(`/api/v1/products/${encodeURIComponent(item.id)}`);
}

export function solicitarOpenSearchEntity3({ item }: { item: SearchResultItem }) {
  return apiClient.request<SaleDetailData>(`/api/v1/sales/${encodeURIComponent(item.id)}`);
}

export function solicitarOpenSearchEntity4({ item }: { item: SearchResultItem }) {
  return apiClient.request(`/api/v1/orders/${encodeURIComponent(item.id)}`);
}

export function solicitarOpenSearchEntity5() {
  return apiClient.request<{ items: Row[] }>("/api/v1/collaboration/tasks");
}

export function solicitarDatos() {
  return apiClient.request<Row>("/api/v1/companies/current");
}

export function solicitarDatos2() {
  return selectorSeed<Row>("branches");
}

export function solicitarDatos3({ path, controller }: { path: string; controller: AbortController }) {
  return apiClient.request<Row[] | { items: Row[]; total_count?: number; count?: number }>(`/api/v1${path}`, { signal: controller.signal });
}

export function solicitarMutate({ path, method, serialized, keys, fingerprint }: { path: string; method: string; serialized: string; keys: React.MutableRefObject<Map<string, string>>; fingerprint: string }) {
  return apiClient.request<Row>(path, { method, body: serialized, headers: { "Idempotency-Key": keys.current.get(fingerprint)! } });
}

export function solicitarOpenEntity() {
  return apiClient.request<Row>("/api/v1/settings");
}

export function solicitarOrganization() {
  return apiClient.request<Row>("/api/v1/companies/current");
}

export function solicitarOrganization2() {
  return selectorSeed<Row>("branches");
}

export function solicitarOrganization3() {
  return apiClient.request<Row>("/api/v1/companies/current/settings");
}
