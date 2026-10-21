import { apiClient } from "../../../api/client";
import type { Row } from "../types/clientes";

export function obtener(customerId: string) {
  return apiClient.request<Row>(`/api/v1/customers/${customerId}`);
}

export function calidad(customerId: string) {
  return apiClient.request<{ score_percentage: number; missing_fields: string[]; alerts: string[]; blocking_purchases: boolean }>(`/api/v1/customers/${customerId}/quality`);
}

export function contactos(customerId: string) {
  return apiClient.request<Row[]>(`/api/v1/customers/${customerId}/contacts`);
}

export function direcciones(customerId: string) {
  return apiClient.request<Row[]>(`/api/v1/customers/${customerId}/addresses`);
}

export function condiciones(customerId: string) {
  return apiClient.request<Row>(`/api/v1/customers/${customerId}/commercial-terms`);
}

export function estadoCuenta(customerId: string) {
  return apiClient.request<{ total_billed: string; total_paid: string; invoices: Row[] }>(`/api/v1/customers/${customerId}/statement`);
}

export function notas(customerId: string) {
  return apiClient.request<Row[]>(`/api/v1/customers/${customerId}/notes`);
}

export function segmentos(customerId: string) {
  return apiClient.request<{ matched_segments: { id: string; name: string }[]; actual_metrics: Row }>(`/api/v1/customers/${customerId}/segments`);
}

export function historial(customerId: string) {
  return apiClient.request<{ timeline: Row[] }>(`/api/v1/customers/${customerId}/history`);
}

export function empresa() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function crearContacto(customerId: string, data: Record<string, FormDataEntryValue>) {
  return apiClient.request(`/api/v1/customers/${customerId}/contacts`, {
    method: "POST",
    body: JSON.stringify({ ...data, is_primary: data.is_primary === "on" })
  });
}

export function eliminarContacto(customerId: string, id: string) {
  return apiClient.request(`/api/v1/customers/${customerId}/contacts/${id}`, { method: "DELETE" });
}

export function crearDireccion(customerId: string, data: Record<string, FormDataEntryValue>) {
  return apiClient.request(`/api/v1/customers/${customerId}/addresses`, {
    method: "POST",
    body: JSON.stringify({ ...data, is_primary: data.is_primary === "on" })
  });
}

export function eliminarDireccion(customerId: string, id: string) {
  return apiClient.request(`/api/v1/customers/${customerId}/addresses/${id}`, { method: "DELETE" });
}

export function crearNota(customerId: string, data: Record<string, FormDataEntryValue>) {
  return apiClient.request(`/api/v1/customers/${customerId}/notes`, {
    method: "POST",
    body: JSON.stringify(data)
  });
}

export function crearActividad(customerId: string, data: Record<string, FormDataEntryValue>) {
  return apiClient.request(`/api/v1/customers/${customerId}/activities`, { method: "POST", body: JSON.stringify({ activity_type: data.activity_type, subject: data.subject, due_date: new Date(String(data.due_date)).toISOString(), reminder_minutes: 15 }) });
}

export function crearOportunidad(customerId: string, data: Record<string, FormDataEntryValue>, companyCurrency: string) {
  return apiClient.request(`/api/v1/customers/${customerId}/opportunities`, { method: "POST", body: JSON.stringify({ title: data.title, estimated_amount: Number(data.estimated_amount || 0), probability: Number(data.probability || 50), currency: companyCurrency }) });
}

export function evaluarCredito(customerId: string, creditTestAmount: string) {
  return apiClient.request<{ allowed: boolean; reason: string; available_credit: string }>(
    `/api/v1/customers/${customerId}/credit-check`,
    { method: "POST", body: JSON.stringify({ amount: Number(creditTestAmount) }) }
  );
}

export function previsualizarFusion(customerId: string, mergeTargetId: string) {
  return apiClient.request<Row>("/api/v1/customers/merge/preview", {
    method: "POST",
    body: JSON.stringify({ primary_customer_id: customerId, duplicate_customer_id: mergeTargetId })
  });
}

export function fusionar(customerId: string, mergeTargetId: string) {
  return apiClient.request("/api/v1/customers/merge", {
    method: "POST",
    body: JSON.stringify({ primary_customer_id: customerId, duplicate_customer_id: mergeTargetId })
  });
}
