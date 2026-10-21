import { CustomSelect } from "../../../ui/components/CustomSelect";
import { Wallet, Calculator } from "lucide-react";
import { useOperatingProfile } from "../../organizacion/components/OperatingProfileContext";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { apiClient } from "../../../api/client";

import type { TeamSection } from "./SalesTeamTab";

import type { SalesRepItem } from "../types/SalesTeamTab";

import { CommissionDetailModal, type CommissionDetail } from "./CommissionDetailModal";

import { CommissionPolicyPanel } from "./CommissionPolicyPanel";

import { CommercialParticipationPanel } from "./CommercialParticipationPanel";

import { CombinedTargetsPanel } from "./CombinedTargetsPanel";

const field = "team-input w-full";

const button = "team-button";

function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudieron consultar las liquidaciones de comisión."; }

export function CommissionCenter({ reps, period, section = "settlements" }: { reps: SalesRepItem[]; period: string; section?: Exclude<TeamSection, "team"> }) {

  const { enabled } = useOperatingProfile();

  const [permissionsReady, setPermissionsReady] = useState(false);

  const [managePermission, setCanManage] = useState(false);

  const canManage = managePermission && enabled("commissions");

  const [sharePermission, setCanShare] = useState(false);

  const canShare = sharePermission && enabled("commissions");

  const [rows, setRows] = useState<CommissionDetail[]>([]);

  const [total, setTotal] = useState(0);

  const [page, setPage] = useState(0);

  const [currency, setCurrency] = useState("");

  const [identifier, setIdentifier] = useState<string | null>(null);

  const [revision, setRevision] = useState(0);

  const [busy, setBusy] = useState(false);

  const [error, setError] = useState("");

  const lock = useRef(false);

  useEffect(() => {

    let active = true;

    void Promise.all([apiClient.getMe(), apiClient.request<{ base_currency: string }>("/api/v1/companies/current")]).then(([me, company]) => { if (active) { setCanManage(Boolean(me.permissions?.includes("organization:manage"))); setCanShare(Boolean(me.permissions?.includes("sales:write"))); setCurrency(company.base_currency); setPermissionsReady(true); } }).catch(cause => { if (active) setError(problem(cause)); });

    return () => { active = false; };

  }, []);

  useEffect(() => { setPage(0); }, [period]);

  useEffect(() => {

    if (section !== "settlements") return;

    const controller = new AbortController();

    const query = new URLSearchParams({ period, limit: "10", offset: String(page * 10) });

    void apiClient.request<{ items: CommissionDetail[]; total_count: number }>(`/api/v1/sales/commissions?${query}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) { setRows(result.items); setTotal(result.total_count); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });

    return () => controller.abort();

  }, [period, page, revision, section]);

  async function calculate(event: FormEvent<HTMLFormElement>) {

    event.preventDefault();

    if (lock.current) return;

    lock.current = true;

    setBusy(true);

    setError("");

    const values = Object.fromEntries(new FormData(event.currentTarget));

    try { const result = await apiClient.request<CommissionDetail>("/api/v1/sales/commissions/calculate", { method: "POST", body: JSON.stringify({ rep_id: values.rep_id, period, currency }) }); setIdentifier(result.settlement_id); setRevision(value => value + 1); }

    catch (cause) { setError(problem(cause)); }

    finally { lock.current = false; setBusy(false); }

  }

  if (!permissionsReady) return <p role="status" className="team-note">{error || "Cargando permisos…"}</p>;
  if (section === "targets") return <CombinedTargetsPanel reps={reps} period={period} canManage={canManage} />;
  if (section === "rules") return canManage ? <CommissionPolicyPanel /> : <p className="rounded-2xl border bg-white p-5 text-sm text-slate-500">No tienes permiso para gestionar las reglas de comisión.</p>;
  if (section === "assignments") return canShare ? <CommercialParticipationPanel reps={reps} canManage={canManage} /> : <p className="rounded-2xl border bg-white p-5 text-sm text-slate-500">No tienes permiso para gestionar las asignaciones comerciales.</p>;
  return <section className="space-y-4"><section className="team-panel"><h2 className="team-panel-title"><Wallet size={20} aria-hidden="true" />Conciliación y liquidaciones de comisiones por moneda</h2><div className="mt-4 space-y-4"><p className="team-note">Período {period}. Cada liquidación conserva las ventas y reglas que la explican. Las observaciones abiertas detienen su aprobación y pago; los documentos que cambien después de aprobar generan diferencias en períodos posteriores.</p>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{canManage && <form className="team-calculation grid items-end gap-4 md:grid-cols-3" onSubmit={calculate}><label className="grid gap-1 text-sm">Vendedor<CustomSelect remote={{ resource: "sales_reps" }} searchable={true} name="rep_id" className={field} required disabled={busy}><option value="">Seleccione vendedor</option>{reps.map(rep => <option key={rep.rep_id} value={rep.rep_id}>{rep.full_name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Moneda de liquidación<input className={field} required pattern="[A-Z]{3}" maxLength={3} value={currency} disabled={busy} onChange={event => setCurrency(event.target.value.toUpperCase())} /></label><button className={`${button} team-primary`} disabled={busy}><Calculator size={16} aria-hidden="true" />Calcular o abrir período</button></form>}<div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{["Vendedor", "Moneda", "Comisión del período", "A pagar", "Saldo por compensar", "Estado", "Detalle"].map(label => <th className="p-2" key={label}>{label}</th>)}</tr></thead><tbody>{rows.map(row => <tr className="border-t" key={row.settlement_id}><td className="p-2">{reps.find(rep => rep.rep_id === row.rep_id)?.full_name || row.rep_id.slice(0, 8)}</td><td className="p-2">{row.currency}</td><td className="p-2">{new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(row.commission_amount))}</td><td className="p-2">{new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(row.payable_amount))}</td><td className="p-2">{new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(row.carried_balance))}</td><td className="p-2">{<span className={`team-status team-status-${row.status}`}>{({ calculated: "Calculada", approved: "Aprobada", paid: "Pagada", pending: "Pendiente", rejected: "Rechazada", observed: "Observada", cancelled: "Cancelada" } as Record<string, string>)[row.status] || row.status}</span>}</td><td className="p-2"><button className={button} onClick={() => setIdentifier(row.settlement_id)}>Revisar</button></td></tr>)}</tbody></table>{rows.length === 0 && <div className="team-empty"><Wallet size={30} aria-hidden="true" /><h3>Sin liquidaciones en este período</h3><p>No hay liquidaciones visibles en este período.</p></div>}</div><div className="team-pagination"><button className={button} disabled={page === 0 || busy} onClick={() => setPage(value => value - 1)}>Anterior</button><span>Página {page + 1} · {total} liquidaciones</span><button className={button} disabled={(page + 1) * 10 >= total || busy} onClick={() => setPage(value => value + 1)}>Siguiente</button><button className={button} disabled={busy} onClick={() => setRevision(value => value + 1)}>Actualizar</button></div></div></section>{identifier && <CommissionDetailModal identifier={identifier} onClose={() => setIdentifier(null)} onChanged={() => setRevision(value => value + 1)} />}</section>;

}

