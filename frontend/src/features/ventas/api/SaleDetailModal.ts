import { apiClient } from "../../../api/client";
import { SaleDetailData } from "../types/SaleDetailModal";

export function solicitarLoadFullSale({ id, signal }: { id: string; signal?: AbortSignal }) {
  return apiClient.request<SaleDetailData>(`/api/v1/sales/${id}`, { signal });
}
