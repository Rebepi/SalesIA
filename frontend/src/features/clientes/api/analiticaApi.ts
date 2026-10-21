import { apiClient } from "../../../api/client";
import type { CustomerAnalyticsItem, CustomerAnalyticsSummary, CustomerCohortItem } from "../types/clientes";
import type { MeasurementContext } from "../../analitica/components/MeasurementDefinitions";

export function consultar(period: string, signal?: AbortSignal) {
  return apiClient.request<{ currency: string; measurement_context?: MeasurementContext; summary: CustomerAnalyticsSummary; items: CustomerAnalyticsItem[]; cohorts: CustomerCohortItem[] }>(
    `/api/v1/analytics/customers?period=${period}`, { signal }
  );
}
