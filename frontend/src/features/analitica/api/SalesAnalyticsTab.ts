import { apiClient } from "../../../api/client";
import { ProductItem } from "../types/SalesAnalyticsTab";
import { SellerItem } from "../types/SalesAnalyticsTab";
import { BranchItem } from "../types/SalesAnalyticsTab";
import { SalesAnalyticsData } from "../types/SalesAnalyticsTab";

export function solicitarDatos() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarDatos2({ period, granularity, currency }: { period: string; granularity: string; currency: string }) {
  return apiClient.request<SalesAnalyticsData>(`/api/v1/analytics/sales?period=${period}&granularity=${granularity}${currency ? `&currency=${currency}` : ""}`);
}

export function solicitarDatos3({ period, currency }: { period: string; currency: string }) {
  return apiClient.request<{ items: ProductItem[] }>(`/api/v1/analytics/products?period=${period}${currency ? `&currency=${currency}` : ""}`);
}

export function solicitarDatos4({ period }: { period: string }) {
  return apiClient.request<{ items: SellerItem[] }>(`/api/v1/analytics/sellers?period=${period}`);
}

export function solicitarDatos5({ period, currency }: { period: string; currency: string }) {
  return apiClient.request<{ items: BranchItem[] }>(`/api/v1/analytics/branches?period=${period}${currency ? `&currency=${currency}` : ""}`);
}
