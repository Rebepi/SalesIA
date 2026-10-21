import { apiClient } from "./client";

export async function selectorSeed<T>(resource: string, scope: Record<string, string> = {}): Promise<T[]> {
  const params = new URLSearchParams({ ...scope, limit: "20" });
  const result = await apiClient.request<{ items: { data: T }[] }>(`/api/v1/selector-options/${resource}?${params}`);
  return result.items.map(item => item.data);
}
