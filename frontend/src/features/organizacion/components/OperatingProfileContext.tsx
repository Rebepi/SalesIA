import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiClient } from "../../../api/client";

export type OperatingProfile = { company_id: string; version: number; profile: string; enabled: string[]; areas: Record<string, { label: string; requires: string[] }>; profiles: Record<string, { label: string; enabled: string[] }> };
export const OPERATING_PROFILE_CHANGED = "salesia:operating-profile-changed";
const Context = createContext<{ profile: OperatingProfile | null; enabled: (area: string) => boolean }>({ profile: null, enabled: () => true });
export const viewAreas: Record<string, string> = { inventory: "inventory", quotations: "quotations", orders: "orders", team: "commissions", team_targets: "commissions", team_rules: "commissions", team_assignments: "commissions", team_settlements: "commissions", receivables: "credit", cash: "cash", cash_movements: "cash", cash_counts: "cash", cash_custody: "cash", cash_petty: "cash", cash_forecast: "cash", warranties: "warranties", expenses: "expenses", payables: "payables", probability: "analytics", datasets: "analytics", variables: "analytics", statistics: "analytics", insights: "analytics", analytics_history: "analytics" };

export function OperatingProfileProvider({ companyId, children }: { companyId: string; children: ReactNode }) {
  const [profile, setProfile] = useState<OperatingProfile | null>(null);
  const [revision, setRevision] = useState(0);
  useEffect(() => { const changed = () => setRevision(value => value + 1); window.addEventListener(OPERATING_PROFILE_CHANGED, changed); return () => window.removeEventListener(OPERATING_PROFILE_CHANGED, changed); }, []);
  useEffect(() => {
    const controller = new AbortController();
    setProfile(null);
    void apiClient.request<OperatingProfile>("/api/v1/organization/operating-profile", { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setProfile(result); }).catch(() => { if (!controller.signal.aborted) setProfile(null); });
    return () => controller.abort();
  }, [companyId, revision]);
  return <Context.Provider value={{ profile, enabled: area => !profile || profile.enabled.includes(area) }}>{children}</Context.Provider>;
}

export function useOperatingProfile() { return useContext(Context); }

export function OperatingSection({ view, children }: { view: string; children: (canOperate: boolean) => ReactNode }) {
  const { enabled } = useOperatingProfile();
  const area = viewAreas[view];
  return <>{children(!area || enabled(area))}</>;
}

export function OperatingAreaNotice({ view }: { view: string }) {
  const { enabled, profile } = useOperatingProfile();
  const area = viewAreas[view];
  return area && !enabled(area) ? <p role="status" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{profile?.areas[area]?.label || "Esta área"} está desactivada en el perfil de la empresa. Puede consultar el historial; para registrar operaciones, habilite el área desde Configuración.</p> : null;
}
