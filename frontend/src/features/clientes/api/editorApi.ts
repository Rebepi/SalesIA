import { apiClient } from "../../../api/client";
import type { CustomerData } from "../types/clientes";

export function buscarDocumento(docNum: string) {
  return apiClient.request<{ items: CustomerData[] }>(`/api/v1/customers?search=${encodeURIComponent(docNum)}`);
}

export function validarDocumento(docNum: string, formData: CustomerData) {
  return apiClient.request<{ valid: boolean; provider: string; external_lookup_ready: boolean }>("/api/v1/customers/fiscal/validate", { method: "POST", body: JSON.stringify({ doc_type: formData.doc_type, doc_number: docNum }) });
}

export function obtenerExistente(candidate: CustomerData) {
  return apiClient.request<CustomerData>(`/api/v1/customers/${candidate.id}`);
}

export function comprobarDuplicados(formData: CustomerData) {
  return apiClient.request<{ exact_matches: CustomerData[]; potential_matches: CustomerData[]; is_exact_duplicate: boolean }>("/api/v1/customers/duplicates/check", { method: "POST", body: JSON.stringify({ doc_type: formData.doc_type, doc_number: formData.doc_number, email: formData.email || null, phone: formData.phone || null, legal_name: formData.legal_name }) });
}

export function guardar(formData: CustomerData, path: string, method: string) {
  return apiClient.request<CustomerData>(path, {
    method,
    body: JSON.stringify({ ...formData, code: formData.code.trim() || undefined })
  });
}
