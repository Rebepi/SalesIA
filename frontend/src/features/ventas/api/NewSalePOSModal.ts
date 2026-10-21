import { apiClient } from "../../../api/client";
import { CheckoutPayment } from "../components/PosPaymentEditor";
import { CustomerItem } from "../types/NewSalePOSModal";
import { ProductItem } from "../types/NewSalePOSModal";
import { SaleCartLine } from "../types/NewSalePOSModal";
import { SerialItem } from "../types/NewSalePOSModal";
import { WarehouseItem } from "../types/NewSalePOSModal";
import { BranchItem } from "../types/NewSalePOSModal";
import { PricingResult } from "../types/NewSalePOSModal";

export function solicitarDatos({ controller, line, customer, couponCode }: { controller: AbortController; line: SaleCartLine; customer: CustomerItem | undefined; couponCode: string }) {
  return apiClient.request<PricingResult>("/api/v1/prices/preview", { method: "POST", signal: controller.signal, body: JSON.stringify({ product_id: line.product.id, quantity: line.quantity, customer_id: customer?.id === "walk-in-default" ? null : customer?.id || null, coupon_code: couponCode.trim() || null }) });
}

export function solicitarDatos2({ params, controller }: { params: URLSearchParams; controller: AbortController }) {
  return apiClient.request<{ items: ProductItem[]; total_count: number }>(`/api/v1/products/search-availability?${params}`, { signal: controller.signal });
}

export function solicitarDatos3({ warehouseId, line }: { warehouseId: string; line: SaleCartLine }) {
  return apiClient.request<{ items: SerialItem[] }>(`/api/v1/inventory/serials?warehouse_id=${warehouseId}&product_id=${line.product.id}`);
}

export function solicitarLoadContext() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarLoadContext2() {
  return apiClient.request<{ default_tax_rate: string; rounding_mode: string; tax_included_in_price: boolean; boleta_dni_threshold?: number }>("/api/v1/settings");
}

export function solicitarLoadContext3() {
  return apiClient.request<WarehouseItem[]>("/api/v1/warehouses?is_active=true");
}

export function solicitarLoadContext4() {
  return apiClient.request<BranchItem[]>("/api/v1/branches?is_active=true");
}

export function solicitarLoadContext5() {
  return apiClient.request<CustomerItem>("/api/v1/customers/walk-in/ensure", { method: "POST" });
}

export function solicitarLoadContext6() {
  return apiClient.request<{ items: { rep_id: string; full_name: string; code: string }[] }>("/api/v1/sales/reps/list?limit=20");
}

export function solicitarLoadContext7({ initialCustomerId }: { initialCustomerId: string }) {
  return apiClient.request<CustomerItem>(`/api/v1/customers/${initialCustomerId}`);
}

export function solicitarLoadContext8({ sourceSaleId }: { sourceSaleId: string }) {
  return apiClient.request<{ customer_id: string; warehouse_id: string; document_type: "RECEIPT" | "INVOICE" | "SALE_NOTE"; is_credit: boolean; status: string; version: number; exchange_rate?: string; notes?: string; delivery_address?: string; internal_observations?: string; coupon_code?: string; sales_rep_id?: string; lines: { product_id: string; sku: string; name: string; quantity: string; unit_price: string; serial_numbers?: string[] }[] }>(`/api/v1/sales/${sourceSaleId}`);
}

export function solicitarLoadContext9({ source }: { source: { customer_id: string; warehouse_id: string; document_type: "RECEIPT" | "INVOICE" | "SALE_NOTE"; is_credit: boolean; status: string; version: number; exchange_rate?: string; notes?: string; delivery_address?: string; internal_observations?: string; coupon_code?: string; sales_rep_id?: string; lines: { product_id: string; sku: string; name: string; quantity: string; unit_price: string; serial_numbers?: string[]; }[]; } }) {
  return apiClient.request<CustomerItem>(`/api/v1/customers/${source.customer_id}`);
}

export function solicitarDatos4({ source, line }: { source: { customer_id: string; warehouse_id: string; document_type: "RECEIPT" | "INVOICE" | "SALE_NOTE"; is_credit: boolean; status: string; version: number; exchange_rate?: string; notes?: string; delivery_address?: string; internal_observations?: string; coupon_code?: string; sales_rep_id?: string; lines: { product_id: string; sku: string; name: string; quantity: string; unit_price: string; serial_numbers?: string[]; }[]; }; line: { product_id: string; sku: string; name: string; quantity: string; unit_price: string; serial_numbers?: string[]; } }) {
  return apiClient.request<{ items: ProductItem[] }>(`/api/v1/products/search-availability?warehouse_id=${source.warehouse_id}&search=${encodeURIComponent(line.sku)}&limit=10&offset=0`);
}

export function solicitarSelectCustomer({ value }: { value: string }) {
  return apiClient.request<CustomerItem>(`/api/v1/customers/${value}`);
}

export function solicitarConfirmSale({ resumeExisting, sourceSaleId, idempotencyKeyRef, customer, warehouseId, selectedWarehouse, currency, isCredit, documentType, couponCode, notes, deliveryAddress, internalObservations, exchangeRate, salesRepId, sourceVersion, cart }: { resumeExisting: boolean; sourceSaleId: string | undefined; idempotencyKeyRef: React.MutableRefObject<`${string}-${string}-${string}-${string}-${string}`>; customer: CustomerItem; warehouseId: string; selectedWarehouse: WarehouseItem; currency: string; isCredit: boolean; documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE"; couponCode: string; notes: string; deliveryAddress: string; internalObservations: string; exchangeRate: string; salesRepId: string; sourceVersion: number | undefined; cart: SaleCartLine[] }) {
  return apiClient.request<{ id?: string; sale_id?: string; version?: number }>(resumeExisting ? `/api/v1/sales/${sourceSaleId}` : "/api/v1/sales", {
    method: resumeExisting ? "PATCH" : "POST",
    headers: { "Idempotency-Key": idempotencyKeyRef.current },
    body: JSON.stringify({
      customer_id: customer.id,
      warehouse_id: warehouseId,
      branch_id: selectedWarehouse.branch_id,
      currency,
      is_credit: isCredit,
      document_type: documentType,
      coupon_code: couponCode.trim() || null,
      notes: notes.trim() || null,
      delivery_address: deliveryAddress.trim() || null,
      internal_observations: internalObservations.trim() || null,
      exchange_rate: Number(exchangeRate || 1),
      sales_rep_id: salesRepId || null,
      version: resumeExisting ? sourceVersion : undefined,
      lines: cart.map(line => ({ product_id: line.product.id, sku: line.product.sku, product_name: line.product.name, quantity: line.quantity, unit_price: line.product.unit_price, tax_rate: line.product.tax_rate, serial_numbers: line.serialNumbers || [] }))
    })
  });
}

export function solicitarConfirmSale2({ saleId, isCredit, response }: { saleId: string; isCredit: boolean; response: { id?: string; sale_id?: string; version?: number; } }) {
  return apiClient.request(`/api/v1/sales/${saleId}/confirm`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ is_credit_sale: isCredit, version: response.version }) });
}

export function solicitarConfirmSale3({ saleId, payment, currency, exchangeRate }: { saleId: string; payment: CheckoutPayment; currency: string; exchangeRate: string }) {
  return apiClient.request("/api/v1/payments", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ sale_id: saleId, payment_method: payment.method, amount: payment.amount, currency, reference_code: payment.referenceCode?.trim() || null, cash_tendered: payment.method === "CASH" ? payment.cashTendered : null, cash_session_id: payment.cashSessionId || null, require_cash_session: payment.method === "CASH", exchange_rate: Number(exchangeRate || 1) }) });
}

export function solicitarSuspendSale({ resumeExisting, sourceSaleId, customer, warehouseId, selectedWarehouse, currency, isCredit, documentType, couponCode, notes, deliveryAddress, internalObservations, exchangeRate, salesRepId, sourceVersion, cart }: { resumeExisting: boolean; sourceSaleId: string | undefined; customer: CustomerItem; warehouseId: string; selectedWarehouse: WarehouseItem; currency: string; isCredit: boolean; documentType: "RECEIPT" | "INVOICE" | "SALE_NOTE"; couponCode: string; notes: string; deliveryAddress: string; internalObservations: string; exchangeRate: string; salesRepId: string; sourceVersion: number | undefined; cart: SaleCartLine[] }) {
  return apiClient.request<{ sale_id: string; number: string }>(resumeExisting ? `/api/v1/sales/${sourceSaleId}` : "/api/v1/sales", { method: resumeExisting ? "PATCH" : "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ customer_id: customer.id, warehouse_id: warehouseId, branch_id: selectedWarehouse.branch_id, currency, is_credit: isCredit, document_type: documentType, coupon_code: couponCode.trim() || null, notes: notes.trim() || "Venta suspendida desde POS", delivery_address: deliveryAddress.trim() || null, internal_observations: internalObservations.trim() || null, exchange_rate: Number(exchangeRate || 1), sales_rep_id: salesRepId || null, version: resumeExisting ? sourceVersion : undefined, lines: cart.map(line => ({ product_id: line.product.id, sku: line.product.sku, product_name: line.product.name, quantity: line.quantity, unit_price: line.product.unit_price, tax_rate: line.product.tax_rate, serial_numbers: line.serialNumbers || [] })) }) });
}
