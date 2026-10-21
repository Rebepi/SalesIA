import { apiClient } from "../../../api/client";
import { SystemNotificationItem } from "../types/NotificationsWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ items: SystemNotificationItem[] }>("/api/v1/notifications?limit=200");
}

export function solicitarHandleMarkAllRead() {
  return apiClient.request<{ marked_read_count: number }>("/api/v1/notifications/read-all", { method: "PATCH" });
}

export function solicitarHandleToggleRead({ notification, read }: { notification: SystemNotificationItem; read: boolean }) {
  return apiClient.request(`/api/v1/notifications/${notification.id}/read`, { method: "PATCH", body: JSON.stringify({ read }) });
}

export function solicitarHandleOpenResource({ notif }: { notif: SystemNotificationItem }) {
  return apiClient.request<{ resource_type: string | null; resource_id: string | null; access_granted: boolean }>(`/api/v1/notifications/${notif.id}/resource`);
}
