import { apiClient } from "../../../api/client";
import { ReceivableItem } from "../types/AccountsReceivableTab";
import { CreditNoteItem } from "../types/AccountsReceivableTab";

export function solicitarOpenReconciliation({ item }: { item: ReceivableItem }) {
  return apiClient.request<CreditNoteItem[]>(`/api/v1/credit-notes?sale_id=${item.sale_id}`);
}
