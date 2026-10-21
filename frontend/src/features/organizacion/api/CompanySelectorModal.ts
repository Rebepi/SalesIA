import { apiClient } from "../../../api/client";

export function solicitarLoadCompanies() {
  return apiClient.request<Record<string, unknown>>("/api/v1/companies/current");
}
