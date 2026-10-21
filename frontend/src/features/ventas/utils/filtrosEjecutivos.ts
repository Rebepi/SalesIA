import type { VentasFilterState } from "../types/ventas";

export function filtrosEjecutivos(defaults: VentasFilterState, search: string): VentasFilterState {
  const params = new URLSearchParams(search);
  const key = params.get("dashboard_evidence");
  if (!["revenue", "margin", "costs", "unassigned"].includes(key || "")) return { ...defaults };
  return {
    ...defaults,
    branch_id: params.get("dashboard_branch") || "",
    currency: params.get("dashboard_currency") || "",
    category: params.get("dashboard_category") || "",
    document_status: "Confirmada",
    date_basis: "confirmed",
    dashboard_period: params.get("dashboard_period") || "30d",
    dashboard_as_of: params.get("dashboard_as_of") || "",
    only_zero_cost: key === "costs",
    only_unassigned: key === "unassigned",
    only_with_lines: key === "margin",
  };
}
