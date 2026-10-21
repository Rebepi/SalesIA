import { apiClient } from "../../../api/client";
import { NotificationItem } from "../types/CollaborationWorkspaceTab";
import { PreferenceItem } from "../types/CollaborationWorkspaceTab";
import { TaskItem } from "../types/CollaborationWorkspaceTab";
import { ApprovalItem } from "../types/CollaborationWorkspaceTab";
import { SavedViewItem } from "../types/CollaborationWorkspaceTab";
import { HelpArticleItem } from "../types/CollaborationWorkspaceTab";

export function solicitarLoadNotifications({ url }: { url: string }) {
  return apiClient.request<{ items: NotificationItem[]; unread_count: number }>(url);
}

export function solicitarLoadPreferences() {
  return apiClient.request<{ preferences: PreferenceItem[] }>("/api/v1/notifications/preferences");
}

export function solicitarLoadTasks() {
  return apiClient.request<{ items: TaskItem[] }>("/api/v1/collaboration/tasks");
}

export function solicitarLoadApprovals() {
  return apiClient.request<{ items: ApprovalItem[] }>("/api/v1/collaboration/approvals");
}

export function solicitarLoadViews() {
  return apiClient.request<{ items: SavedViewItem[] }>("/api/v1/collaboration/saved-views?resource_type=sales");
}

export function solicitarLoadHelp() {
  return apiClient.request<{ articles: HelpArticleItem[] }>("/api/v1/help/contextual");
}

export function solicitarMarkRead({ id }: { id: string }) {
  return apiClient.request(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
}

export function solicitarTogglePreference({ pref }: { pref: PreferenceItem }) {
  return apiClient.request("/api/v1/notifications/preferences", {
    method: "PUT",
    body: JSON.stringify({ category: pref.category, channel: pref.channel, enabled: !pref.enabled })
  });
}

export function solicitarCreateTask({ newTaskTitle }: { newTaskTitle: string }) {
  return apiClient.request("/api/v1/collaboration/tasks", {
    method: "POST",
    body: JSON.stringify({ title: newTaskTitle.trim(), priority: "normal" })
  });
}

export function solicitarCompleteTask({ id }: { id: string }) {
  return apiClient.request(`/api/v1/collaboration/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status: "completed", resolution_notes: "Completada por usuario" })
  });
}

export function solicitarDecideApproval({ id, decision, version }: { id: string; decision: "approved" | "rejected"; version: number }) {
  return apiClient.request(`/api/v1/collaboration/approvals/${id}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, reason: "Aprobado en bandeja de operaciones", current_document_version: version })
  });
}

export function solicitarCreateView({ newViewName }: { newViewName: string }) {
  return apiClient.request("/api/v1/collaboration/saved-views", {
    method: "POST",
    body: JSON.stringify({
      resource_type: "sales",
      name: newViewName.trim(),
      config_json: JSON.stringify({ filters: ["status=confirmed"], density: "compact" }),
      schema_version: 2
    })
  });
}
