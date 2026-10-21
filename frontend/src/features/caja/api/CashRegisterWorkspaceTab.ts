import { apiClient } from "../../../api/client";
import { CashSession } from "../types/CashRegisterWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ branch_id: string; name: string; code: string }[]>("/api/v1/branches?is_active=true");
}

export function solicitarDatos2() {
  return apiClient.request<{ base_currency: string }>("/api/v1/companies/current");
}

export function solicitarHandleOpenSession({ data }: { data: FormData }) {
  return apiClient.request("/api/v1/cash-sessions", {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      branch_id: String(data.get("branch_id")),
      terminal_code: String(data.get("terminal_code")),
      opening_balance: String(data.get("opening_balance")),
      currency: String(data.get("currency") || "").trim().toUpperCase() || null
    })
  });
}

export function solicitarHandleNewMovement({ activeSession, data }: { activeSession: CashSession; data: FormData }) {
  return apiClient.request(`/api/v1/cash-sessions/${activeSession.id}/movements`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      movement_type: String(data.get("movement_type")),
      amount: Number(data.get("amount")),
      reason: String(data.get("reason"))
    })
  });
}

export function solicitarHandleBlindCount({ activeSession, data }: { activeSession: CashSession; data: FormData }) {
  return apiClient.request<{ session_id: string; counted_cash: string; requires_approval: boolean }>(
    `/api/v1/cash-sessions/${activeSession.id}/blind-count`,
    {
      method: "POST",
      body: JSON.stringify({
        counted_cash: String(data.get("counted_cash")), denominations: JSON.parse(String(data.get("denominations_json") || "{}")), non_cash_totals: JSON.parse(String(data.get("non_cash_json") || "{}"))
      })
    }
  );
}

export function solicitarHandleApproveDifference({ activeSession, data }: { activeSession: CashSession; data: FormData }) {
  return apiClient.request(`/api/v1/cash-sessions/${activeSession.id}/approve-difference`, {
    method: "POST",
    body: JSON.stringify({
      approved: String(data.get("decision")) !== "reject",
      control_version: activeSession.control.version,
      notes: String(data.get("notes"))
    })
  });
}

export function solicitarHandleCloseSession({ activeSession, data }: { activeSession: CashSession; data: FormData }) {
  return apiClient.request(`/api/v1/cash-sessions/${activeSession.id}/close`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({
      counted_balance: String(data.get("counted_balance")),
      notes: String(data.get("notes") || "") || null
    })
  });
}
