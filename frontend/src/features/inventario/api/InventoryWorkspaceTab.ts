import { selectorSeed } from "../../../api/selectorSeed";
import { apiClient } from "../../../api/client";
import { Warehouse } from "../types/InventoryWorkspaceTab";
import { TransferItem } from "../types/InventoryWorkspaceTab";
import { CountItem } from "../types/InventoryWorkspaceTab";
import { LotItem } from "../types/InventoryWorkspaceTab";
import { SerialItem } from "../types/InventoryWorkspaceTab";
import { LocationItem } from "../types/InventoryWorkspaceTab";
import { RuleItem } from "../types/InventoryWorkspaceTab";
import { AlertItem } from "../types/InventoryWorkspaceTab";
import { QuarantineItem } from "../types/InventoryWorkspaceTab";

export function solicitarDatos() {
  return selectorSeed<Warehouse>("warehouses");
}

export function solicitarDatos2() {
  return apiClient.request<{ items: TransferItem[] }>("/api/v1/inventory/transfers?limit=50");
}

export function solicitarDatos3({ whParam }: { whParam: string }) {
  return apiClient.request<{ items: CountItem[] }>(`/api/v1/inventory/counts?limit=50${whParam}`);
}

export function solicitarDatos4() {
  return apiClient.request<{ items: LotItem[] }>("/api/v1/inventory/lots");
}

export function solicitarDatos5() {
  return apiClient.request<{ items: SerialItem[] }>("/api/v1/inventory/serials");
}

export function solicitarDatos6({ whParam }: { whParam: string }) {
  return apiClient.request<{ items: LocationItem[] }>(`/api/v1/inventory/locations?limit=100${whParam}`);
}

export function solicitarDatos7() {
  return apiClient.request<{ items: RuleItem[] }>("/api/v1/inventory/rules");
}

export function solicitarDatos8() {
  return apiClient.request<{ items: AlertItem[] }>("/api/v1/inventory/alerts");
}

export function solicitarDatos9() {
  return apiClient.request<{ items: QuarantineItem[] }>("/api/v1/inventory/quarantine");
}

export function solicitarHandleDispatchTransfer({ transferId }: { transferId: string }) {
  return apiClient.request(`/api/v1/inventory/transfers/${transferId}/dispatch`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() }
  });
}

export function solicitarHandleCreateCount({ whId, notes, countProductIds }: { whId: string; notes: string; countProductIds: string[] }) {
  return apiClient.request("/api/v1/inventory/counts", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ warehouse_id: whId, notes, scope: countProductIds.length ? "CYCLE" : "FULL", is_blind: true, product_ids: countProductIds.length ? countProductIds : undefined })
  });
}

export function solicitarHandleApproveCount({ countId }: { countId: string }) {
  return apiClient.request(`/api/v1/inventory/counts/${countId}/approve`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() }
  });
}

export function solicitarHandleRecalculateAlerts() {
  return apiClient.request<{ active_alerts_count: number }>("/api/v1/inventory/alerts/recalculate", { method: "POST" });
}

export function solicitarHandleRunReconcile({ whId, prodId }: { whId: string; prodId: string }) {
  return apiClient.request<{ status: string; discrepancy_delta: string; ledger_balance: string; cached_stock_balance: string }>("/api/v1/inventory/reconcile", {
    method: "POST",
    body: JSON.stringify({ warehouse_id: whId, product_id: prodId })
  });
}

export function solicitarHandleClassifyQuarantine({ id, action }: { id: string; action: "RESTOCK" | "SCRAP" }) {
  return apiClient.request(`/api/v1/inventory/quarantine/${id}/classify`, {
    method: "POST",
    body: JSON.stringify({ action, notes: action === "RESTOCK" ? "Aprobado para stock" : "Merma justificada" })
  });
}

export function solicitarBlockLot({ id }: { id: string }) {
  return apiClient.request(`/api/v1/inventory/lots/${id}/block`, { method: "POST" });
}

export function solicitarDeactivateRule({ id }: { id: string }) {
  return apiClient.request(`/api/v1/inventory/rules/${id}/deactivate`, { method: "POST" });
}
