import { selectorSeed } from "../../../api/selectorSeed";
import { apiClient } from "../../../api/client";
import { QuotationItem } from "../types/QuotationsWorkspaceTab";
import { CustomerItem } from "../types/QuotationsWorkspaceTab";
import { QuotationLine } from "../types/QuotationsWorkspaceTab";

export function solicitarLoadContext() {
  return selectorSeed<{ warehouse_id: string; name: string; code?: string; branch_id?: string }>("warehouses", { active_only: "true" });
}

export function solicitarLoadContext2() {
  return selectorSeed<{ branch_id: string; name: string; code?: string }>("branches", { active_only: "true" });
}

export function solicitarLoadContext3() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarLoadContext4() {
  return apiClient.request<{ default_tax_rate: string }>("/api/v1/settings");
}

export function solicitarLoadContext5() {
  return apiClient.request<{ items?: Array<{ rep_id: string; full_name?: string; name?: string }> }>("/api/v1/sales/reps/list?period=month&limit=20");
}

export function solicitarOpenCreateModal({ contextualCustomerId }: { contextualCustomerId: string }) {
  return apiClient.request<CustomerItem>(`/api/v1/customers/${contextualCustomerId}`);
}

export function solicitarHandleCreateQuotation({ customer, branchId, currency, validDays, paymentTerms, deliveryTerms, notes, specialConditions, sellerId, lines }: { customer: CustomerItem; branchId: string; currency: string; validDays: string; paymentTerms: string; deliveryTerms: string; notes: string; specialConditions: string; sellerId: string; lines: QuotationLine[] }) {
  return apiClient.request("/api/v1/quotations", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ customer_id: customer.id, branch_id: branchId, currency, valid_until: new Date(Date.now() + Number(validDays) * 86400000).toISOString(), payment_terms_days: Number(paymentTerms), delivery_terms: deliveryTerms || null, notes: notes || null, special_conditions: specialConditions || null, seller_id: sellerId || null, lines: lines.map(({ product_id, quantity, discount_pct }) => ({ product_id, quantity, discount_pct: discount_pct || "0" })) })
  });
}

export function solicitarHandleAccept({ quotation }: { quotation: QuotationItem }) {
  return apiClient.request(`/api/v1/quotations/${quotation.quotation_id || quotation.id}/accept`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
}

export function solicitarHandleConvert({ conversion, conversionWarehouseId }: { conversion: QuotationItem; conversionWarehouseId: string }) {
  return apiClient.request(`/api/v1/quotations/${conversion.quotation_id || conversion.id}/convert?warehouse_id=${conversionWarehouseId}`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
}

export function solicitarHandleNewVersion({ quotation }: { quotation: QuotationItem }) {
  return apiClient.request<QuotationItem>(`/api/v1/quotations/${quotation.quotation_id || quotation.id}`);
}

export function solicitarHandleNewVersion2({ quotation, lines }: { quotation: QuotationItem; lines: NonNullable<QuotationItem["lines"]> }) {
  return apiClient.request(`/api/v1/quotations/${quotation.quotation_id || quotation.id}/versions`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ lines: lines.map(line => ({ product_id: line.product_id, quantity: line.quantity, discount_pct: line.discount_pct || "0" })) }) });
}

export function solicitarOpenPreview({ quotation }: { quotation: QuotationItem }) {
  return apiClient.request<QuotationItem>(`/api/v1/quotations/${quotation.quotation_id || quotation.id}/preview`);
}

export function solicitarSubmitSend({ sendQuotation, form }: { sendQuotation: QuotationItem; form: FormData }) {
  return apiClient.request<{ integration_url?: string }>(`/api/v1/quotations/${sendQuotation.quotation_id || sendQuotation.id}/send`, { method: "POST", body: JSON.stringify({ channel: String(form.get("channel")), recipient: String(form.get("recipient") || ""), message: String(form.get("message") || "") || null }) });
}
