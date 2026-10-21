import { selectorSeed } from "../../../api/selectorSeed";
import { apiClient } from "../../../api/client";
import { Row } from "../types/SalesTeamTab";
import { SalesRepItem } from "../types/SalesTeamTab";

export function solicitarLoadData({ period, teamQuery, page = 0, pageSize = 25, search = "" }: { period: string; teamQuery: string; page?: number; pageSize?: number; search?: string }) {
  return apiClient.request<{ items: SalesRepItem[]; count: number }>(`/api/v1/sales/reps/list?period=${period}${teamQuery}&limit=${pageSize}&offset=${page * pageSize}&search=${encodeURIComponent(search)}`);
}

export function solicitarLoadData2() {
  return selectorSeed<Row>("branches");
}

export function solicitarSaveRep({ payload }: { payload: { code: string; full_name: string; branch_id: string | null; team: string | null; territory: string; monthly_quota: string; is_active: boolean; } }) {
  return apiClient.request("/api/v1/sales/reps", { method: "POST", body: JSON.stringify(payload) });
}

export function solicitarSaveRep2({ repModal, payload }: { repModal: SalesRepItem; payload: { code: string; full_name: string; branch_id: string | null; team: string | null; territory: string; monthly_quota: string; is_active: boolean; } }) {
  return apiClient.request(`/api/v1/sales/reps/${repModal.rep_id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function solicitarSaveTarget({ payload }: { payload: { representative_id: string; period: string; target_type: string; target_value: string; currency: string; scope: string; } }) {
  return apiClient.request("/api/v1/sales/targets", { method: "POST", body: JSON.stringify(payload) });
}

export function solicitarOpenPortfolio({ rep }: { rep: SalesRepItem }) {
  return apiClient.request<Row>(`/api/v1/sales/reps/${rep.rep_id}/portfolio`);
}

export function solicitarExecuteReassign({ portfolioModal, targetRepId, reason }: { portfolioModal: { rep: SalesRepItem; preview: Row | null; }; targetRepId: string; reason: string }) {
  return apiClient.request(`/api/v1/sales/reps/${portfolioModal.rep.rep_id}/reassign-portfolio`, {
    method: "POST",
    body: JSON.stringify({ target_rep_id: targetRepId, reason })
  });
}

export function solicitarOpenCommissions({ rep, period }: { rep: SalesRepItem; period: string }) {
  return apiClient.request<Row>("/api/v1/sales/commissions/calculate", {
    method: "POST",
    body: JSON.stringify({ rep_id: rep.rep_id, period })
  });
}

export function solicitarApproveCommission({ settlement }: { settlement: Row }) {
  return apiClient.request<Row>(`/api/v1/sales/commissions/${settlement.settlement_id}/approve`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ expected_version: settlement.version, reason: "Revisión de la liquidación comercial" }) });
}

export function solicitarPayCommission({ settlement }: { settlement: Row }) {
  return apiClient.request<Row>(`/api/v1/sales/commissions/${settlement.settlement_id}/pay`, { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ expected_version: settlement.version, reason: "Registro del pago de la comisión", payout_reference: settlement.payout_reference }) });
}
