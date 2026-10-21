import { apiClient } from "../../../api/client";
import { Supplier } from "../types/PurchasesWorkspaceTab";
import { PurchaseOrder } from "../types/PurchasesWorkspaceTab";
import { PurchaseRequisition } from "../types/PurchasesWorkspaceTab";
import { ReplenishmentSuggestion } from "../types/PurchasesWorkspaceTab";
import { SupplierPerformance } from "../types/PurchasesWorkspaceTab";
import { ReceiptActionChoice } from "../types/PurchasesWorkspaceTab";
import { ProcessTimeline } from "../types/PurchasesWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ warehouse_id: string; name: string; code: string }[]>("/api/v1/warehouses?is_active=true");
}

export function solicitarDatos2() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarDatos3() {
  return apiClient.request<{ default_tax_rate: string }>("/api/v1/settings");
}

export function solicitarDatos4() {
  return apiClient.request<{ items: PurchaseRequisition[] }>("/api/v1/purchases/requisitions");
}

export function solicitarDatos5({ replenishmentWarehouse }: { replenishmentWarehouse: string }) {
  return apiClient.request<{ suggestions: ReplenishmentSuggestion[] }>(`/api/v1/purchases/replenishment-suggestions${replenishmentWarehouse ? `?warehouse_id=${replenishmentWarehouse}` : ""}`);
}

export function solicitarHandleCreateSupplier({ data, companyCurrency }: { data: FormData; companyCurrency: string }) {
  return apiClient.request<Supplier & Record<string, unknown>>("/api/v1/suppliers", {
    method: "POST",
    body: JSON.stringify({
      tax_id: String(data.get("tax_id")),
      legal_name: String(data.get("legal_name")),
      contact_name: String(data.get("contact_name") || "") || null,
      email: String(data.get("email") || "") || null,
      phone: String(data.get("phone") || "") || null,
      payment_terms_days: Number(data.get("payment_terms_days") || 30),
      currency: String(data.get("currency") || companyCurrency),
      bank_name: String(data.get("bank_name") || "") || null,
      bank_account: String(data.get("bank_account") || "") || null,
      notes: String(data.get("notes") || "") || null
    })
  });
}

export function solicitarHandleApproveOrder({ orderId }: { orderId: string }) {
  return apiClient.request(`/api/v1/purchase-orders/${orderId}/approve`, { method: "POST" });
}

export function solicitarDatos6({ activeOrder, controller }: { activeOrder: PurchaseOrder; controller: AbortController }) {
  return apiClient.request<{ receipts: ReceiptActionChoice[] }>(`/api/v1/purchase-orders/${activeOrder.id}/receiving-context`, { signal: controller.signal });
}

export function solicitarHandleLandedCost({ targetReceiptId, receiptActionKey, data }: { targetReceiptId: string; receiptActionKey: React.MutableRefObject<`${string}-${string}-${string}-${string}-${string}`>; data: FormData }) {
  return apiClient.request(`/api/v1/goods-receipts/${targetReceiptId}/landed-cost`, {
    method: "POST",
    headers: { "Idempotency-Key": receiptActionKey.current },
    body: JSON.stringify({
      charges: [{
        charge_type: String(data.get("charge_type") || "FREIGHT"),
        amount: String(data.get("amount")),
        allocation_method: String(data.get("allocation_method") || "VALUE"),
        notes: String(data.get("notes") || "")
      }]
    })
  });
}

export function solicitarHandlePurchaseReturn({ receiptActionKey, selectedReceipt, activeOrder, line, data }: { receiptActionKey: React.MutableRefObject<`${string}-${string}-${string}-${string}-${string}`>; selectedReceipt: ReceiptActionChoice; activeOrder: PurchaseOrder; line: { product_id: string; name: string; sku: string; quantity: string; returnable_quantity: string; unit_cost: string; lots: { lot_id: string; lot_code: string; quantity: string; }[]; serial_numbers: string[]; }; data: FormData }) {
  return apiClient.request("/api/v1/purchases/returns", {
    method: "POST",
    headers: { "Idempotency-Key": receiptActionKey.current },
    body: JSON.stringify({
      goods_receipt_id: selectedReceipt.id,
      warehouse_id: activeOrder.warehouse_id,
      items: [{
        product_id: line.product_id,
        quantity: String(data.get("quantity")),
        lot_id: String(data.get("lot_id") || "") || null,
        serial_numbers: String(data.get("serial_numbers") || "").split(/[\r\n,;]+/).map(value => value.trim()).filter(Boolean)
      }],
      reason: String(data.get("reason")),
    })
  });
}

export function solicitarHandleThreeWayMatch({ activeOrder, data }: { activeOrder: PurchaseOrder; data: FormData }) {
  return apiClient.request<{ status: string; discrepancy_amount: string; requires_review: boolean }>(
    `/api/v1/purchase-orders/${activeOrder.id}/three-way-match`,
    {
      method: "POST",
      body: JSON.stringify({
        supplier_invoice_number: String(data.get("supplier_invoice_number")),
        invoice_amount: String(data.get("invoice_amount")),
        notes: String(data.get("notes") || "")
      })
    }
  );
}

export function solicitarHandleViewPerformance({ supplierId }: { supplierId: string }) {
  return apiClient.request<SupplierPerformance>(`/api/v1/suppliers/${supplierId}/performance`);
}

export function solicitarHandleViewTimeline({ orderId }: { orderId: string }) {
  return apiClient.request<ProcessTimeline>(`/api/v1/purchase-orders/${orderId}/process-timeline`);
}
