import { apiClient } from "../../../api/client";
import { DeliveryItem } from "../types/DeliveriesWorkspaceTab";
import { ProofOfDeliveryData } from "../types/DeliveriesWorkspaceTab";

export function solicitarOpenCreateDelivery() {
  return apiClient.request<{ items: { sale_id: string; number: string; total_amount: string; currency: string; warehouse_id?: string | null }[] }>("/api/v1/sales?status=confirmed&page_size=100");
}

export function solicitarOpenCreateDelivery2() {
  return apiClient.request<{ warehouse_id: string; name: string; code: string }[]>("/api/v1/warehouses?is_active=true");
}

export function solicitarOpenCreateDelivery3() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarHandleCreateDelivery({ data }: { data: FormData }) {
  return apiClient.request("/api/v1/deliveries", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      sale_id: String(data.get("sale_id")),
      warehouse_id: String(data.get("warehouse_id")),
      recipient_name: String(data.get("recipient_name")),
      delivery_address: String(data.get("delivery_address")),
      recipient_phone: String(data.get("recipient_phone") || "") || null,
      carrier: String(data.get("carrier")),
      tracking_number: String(data.get("tracking_number")),
      tracking_url: String(data.get("tracking_url") || "") || null,
      shipping_fee_charged: String(data.get("shipping_fee_charged") || "0"),
      logistics_cost: String(data.get("logistics_cost") || "0"),
      estimated_delivery_date: String(data.get("estimated_delivery_date") || "") || null,
      is_guaranteed: data.get("is_guaranteed") === "true",
      notes: String(data.get("notes") || "") || null
    })
  });
}

export function solicitarHandleDispatch({ deliveryId }: { deliveryId: string }) {
  return apiClient.request(`/api/v1/deliveries/${deliveryId}/dispatch`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() }
  });
}

export function solicitarHandleAddTrackingEvent({ activeDelivery, data }: { activeDelivery: DeliveryItem; data: FormData }) {
  return apiClient.request(`/api/v1/deliveries/${activeDelivery.id}/tracking-events`, {
    method: "POST",
    body: JSON.stringify({
      event_code: String(data.get("event_code")),
      event_status: String(data.get("event_status")),
      description: String(data.get("description")),
      location: String(data.get("location") || "") || null
    })
  });
}

export function solicitarHandleRecordPod({ activeDelivery, data }: { activeDelivery: DeliveryItem; data: FormData }) {
  return apiClient.request(`/api/v1/deliveries/${activeDelivery.id}/proof-of-delivery`, {
    method: "POST",
    body: JSON.stringify({
      outside_window_reason: String(data.get("outside_window_reason") || ""),
      received_by_name: String(data.get("received_by_name")),
      received_by_id_doc: String(data.get("received_by_id_doc") || "") || null,
      signature_data: String(data.get("signature_data") || "") || null,
      photo_url: String(data.get("photo_url") || "") || null,
      notes: String(data.get("notes") || "") || null
    })
  });
}

export function solicitarHandleViewPod({ deliveryId }: { deliveryId: string }) {
  return apiClient.request<ProofOfDeliveryData>(`/api/v1/deliveries/${deliveryId}/proof-of-delivery`);
}

export function solicitarHandleRecordIncident({ activeDelivery, data }: { activeDelivery: DeliveryItem; data: FormData }) {
  return apiClient.request(`/api/v1/deliveries/${activeDelivery.id}/incidents`, {
    method: "POST",
    body: JSON.stringify({
      incident_type: String(data.get("incident_type")),
      description: String(data.get("description")),
      rescheduled_date: String(data.get("rescheduled_date") || "") || null
    })
  });
}

export function solicitarHandleCancel({ deliveryId }: { deliveryId: string }) {
  return apiClient.request(`/api/v1/deliveries/${deliveryId}/cancel`, { method: "POST" });
}

export function solicitarHandleIntercept({ deliveryId }: { deliveryId: string }) {
  return apiClient.request(`/api/v1/deliveries/${deliveryId}/intercept`, {
    method: "POST",
    body: JSON.stringify({
      reason: "Solicitud urgente de intercepción y retorno comercial."
    })
  });
}
