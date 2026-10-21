import { apiClient } from "../../../api/client";
import { PersonalTask } from "../types/PersonalWorkspaceTab";
import { AssignedOrder } from "../types/PersonalWorkspaceTab";
import { AssignedCustomer } from "../types/PersonalWorkspaceTab";

export function solicitarDatos({ param }: { param: string }) {
  return apiClient.request<{ items: Array<{ id: string; legal_name: string; doc_number: string }> }>(
    `/api/v1/customers?limit=6${param}`
  );
}

export function solicitarDatos2({ param, branchParam }: { param: string; branchParam: string }) {
  return apiClient.request<Array<{ order_id: string; order_number: string; customer_name?: string }>>(
    `/api/v1/orders?limit=6${param}${branchParam}`
  );
}

export function solicitarDatos3({ userId, searchParam }: { userId: string; searchParam: string }) {
  return apiClient.request<{
    items: Array<{
      id: string;
      title: string;
      description?: string | null;
      due_date: string | null;
      priority: "low" | "normal" | "high" | "urgent";
      status: "pending" | "in_progress" | "completed" | "cancelled";
      creator_id?: string;
      assignee_id?: string;
      resource_type?: string | null;
      resource_id?: string | null;
      resource_name?: string | null;
      created_at?: string;
      updated_at?: string;
    }>;
    total_count: number;
  }>(`/api/v1/collaboration/tasks?assignee_id=${userId}${searchParam}`);
}

export function solicitarDatos4({ period, branchParam }: { period: string; branchParam: string }) {
  return apiClient.request<{
    items: Array<{
      representative_id: string;
      user_id: string | null;
      full_name?: string;
      target_quota: string | number | null;
      current_sales: string | number;
      gross_sales?: string | number;
      refunds?: string | number;
      net_sales?: string | number;
      quota_attainment_pct: string | number | null;
    }>;
  }>(`/api/v1/sales/reps/list?period=${period}${branchParam}`);
}

export function solicitarDatos5({ params }: { params: URLSearchParams }) {
  return apiClient.request<AssignedOrder[]>(`/api/v1/orders?${params.toString()}`);
}

export function solicitarDatos6({ params }: { params: URLSearchParams }) {
  return apiClient.request<{ items: AssignedCustomer[]; total?: number }>(`/api/v1/customers?${params.toString()}`);
}

export function solicitarHandleToggleTaskStatus({ task, nextStatus }: { task: PersonalTask; nextStatus: "pending" | "completed" }) {
  return apiClient.request(`/api/v1/collaboration/tasks/${task.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: nextStatus,
      resolution_notes: nextStatus === "completed" ? "Completada desde Mi Trabajo" : "Reabierta desde Mi Trabajo"
    })
  });
}

export function solicitarHandleCreateQuickTask({ payload }: { payload: { title: string; assignee_id: string; priority: "low" | "normal" | "high" | "urgent"; description?: string; due_date?: string; resource_type?: string; resource_id?: string; } }) {
  return apiClient.request<PersonalTask>("/api/v1/collaboration/tasks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function solicitarHandleSaveEditTask({ taskToEdit }: { taskToEdit: PersonalTask }) {
  return apiClient.request<PersonalTask>(`/api/v1/collaboration/tasks/${taskToEdit.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: taskToEdit.title,
      description: taskToEdit.description || "",
      priority: taskToEdit.priority,
      status: taskToEdit.status,
      due_date: taskToEdit.due_date ? `${taskToEdit.due_date.slice(0, 10)}T23:59:59` : null
    })
  });
}

export function solicitarHandleConfirmDeleteTask({ taskToDelete }: { taskToDelete: PersonalTask }) {
  return apiClient.request(`/api/v1/collaboration/tasks/${taskToDelete.id}`, {
    method: "DELETE"
  });
}
