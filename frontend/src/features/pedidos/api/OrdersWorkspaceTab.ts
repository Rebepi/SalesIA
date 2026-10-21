import { apiClient } from "../../../api/client";
import { OrderItem } from "../types/OrdersWorkspaceTab";
import { CustomerChoice } from "../types/OrdersWorkspaceTab";
import { ProductChoice } from "../types/OrdersWorkspaceTab";
import { BranchChoice } from "../types/OrdersWorkspaceTab";
import { WarehouseChoice } from "../types/OrdersWorkspaceTab";

export function solicitarOpenContextOrder({ id }: { id: string }) {
  return apiClient.request<OrderItem>(`/api/v1/orders/${encodeURIComponent(id)}`);
}

export function solicitarDatos() {
  return apiClient.request<BranchChoice[]>("/api/v1/branches");
}

export function solicitarDatos2() {
  return apiClient.request<WarehouseChoice[] | { items?: WarehouseChoice[] }>("/api/v1/warehouses");
}

export function solicitarDatos3() {
  return apiClient.request<{ base_currency?: string; default_tax_rate?: string }>("/api/v1/companies/current");
}

export function solicitarDatos4({ customerId }: { customerId: string }) {
  return apiClient.request<CustomerChoice>(`/api/v1/customers/${customerId}`);
}

export function solicitarDatos5({ context }: { context: { product_id: string; warehouse_id: string; } }) {
  return apiClient.request<ProductChoice>(`/api/v1/products/${context.product_id}`);
}

export function solicitarDatos6() {
  return apiClient.request<WarehouseChoice[]>("/api/v1/warehouses");
}

export function solicitarHandleConfirmAndReserve({ order }: { order: OrderItem }) {
  return apiClient.request(`/api/v1/orders/${order.id}/confirm`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ allow_backorder: true, reservation_days: 7 })
  });
}

export function solicitarHandleFulfillSubmit({ fulfillModal, items }: { fulfillModal: OrderItem; items: { product_id: string; quantity: string; order_line_number?: number; serial_numbers?: string[]; }[] }) {
  return apiClient.request(`/api/v1/orders/${fulfillModal.id}/fulfill-partial`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ fulfilled_items: items })
  });
}

export function solicitarCreateOrder({ editingOrder, payload }: { editingOrder: OrderItem | null; payload: { customer_id: string; branch_id: string; warehouse_id: string; currency: string; payment_terms_days: number; delivery_terms: string | null; customer_po_number: string | null; allow_backorder: boolean; lines: { product_id: string; quantity: string; discount_pct: string; }[]; } }) {
  return apiClient.request(editingOrder ? `/api/v1/orders/${editingOrder.id}/lines` : "/api/v1/orders", { method: editingOrder ? "PUT" : "POST", headers: editingOrder ? undefined : { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(editingOrder ? { lines: payload.lines } : payload) });
}

export function solicitarOrderAction({ id, action, headers, body }: { id: string | undefined; action: "approve" | "release-reservation" | "renew-reservation" | "cancel" | "clone" | "picking"; headers: { "Idempotency-Key": `${string}-${string}-${string}-${string}-${string}`; } | undefined; body: string | undefined }) {
  return apiClient.request<OrderItem | { status?: string }>(`/api/v1/orders/${id}/${action}`, { method: "POST", headers, body });
}

export function solicitarScanPicking({ scanOrder, target, scanCode }: { scanOrder: OrderItem; target: { product_id: string; sku: string; name: string; expected_quantity: string; picked_quantity: string; verified: boolean; }; scanCode: string }) {
  return apiClient.request<OrderItem["picking"]>(`/api/v1/orders/${scanOrder.id}/picking/scan`, { method: "POST", body: JSON.stringify({ product_id: target.product_id, scanned_code: scanCode || target.sku, quantity: 1 }) });
}

export function solicitarCompletePicking({ scanOrder }: { scanOrder: OrderItem }) {
  return apiClient.request(`/api/v1/orders/${scanOrder.id}/picking/complete`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
}

export function solicitarOpenShortages({ order, shortages }: { order: OrderItem; shortages: { product_id: string; sku: string; name: string; missing_quantity: string; alternatives: Array<{ warehouse_id: string; warehouse_name: string; available_quantity: string; }>; }[] }) {
  return apiClient.request<{ shortages: typeof shortages }>(`/api/v1/orders/${order.id}/shortages`);
}

export function solicitarResolveShortage({ shortageOrder, productId, action, warehouseIdValue, substituteProductId, estimated }: { shortageOrder: OrderItem; productId: string; action: string; warehouseIdValue: string | undefined; substituteProductId: string | undefined; estimated: string | null | undefined }) {
  return apiClient.request(`/api/v1/orders/${shortageOrder.id}/resolve-shortage`, { method: "POST", body: JSON.stringify({ product_id: productId, action, warehouse_id: warehouseIdValue || null, substitute_product_id: substituteProductId || null, estimated_delivery_date: estimated || null }) });
}
