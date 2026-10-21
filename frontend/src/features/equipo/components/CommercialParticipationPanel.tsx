import { CustomSelect } from "../../../ui/components/CustomSelect";
import { UsersRound } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";
import type { SalesRepItem } from "../types/SalesTeamTab";

type Sale = Record<string, unknown> & { id?: string; sale_id?: string; series?: string; number?: number; document_number?: string };
type Share = { representative_id: string; role: string; percentage: string; name?: string; team?: string | null };
type Participation = { sale_id: string; sale_version: number; status: string; document_number: string; original_representative_id: string | null; frozen?: boolean; participants?: Share[]; policy?: { version: number }; reason?: string };
type Coverage = { id: string; version: number; representative_id: string; replacement_id: string; starts_on: string; ends_on: string; percentage: string; reason: string; status: string; actor: string };
const field = "team-input w-full";
const button = "team-button";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo actualizar la participación comercial."; }

export function CommercialParticipationPanel({ reps, canManage }: { reps: SalesRepItem[]; canManage: boolean }) {
  const [tab, setTab] = useState<"shares" | "replacements">("shares");
  const [saleId, setSaleId] = useState("");
  const [participation, setParticipation] = useState<Participation | null>(null);
  const [shares, setShares] = useState<Share[]>([]);
  const [coverages, setCoverages] = useState<Coverage[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => {
    const controller = new AbortController();
    if (!saleId) { setParticipation(null); setShares([]); return () => controller.abort(); }
    void apiClient.request<Participation>(`/api/v1/sales/${saleId}/commission-participation`, { signal: controller.signal }).then(row => { if (!controller.signal.aborted) { setParticipation(row); setShares(row.participants?.length ? row.participants : [{ representative_id: row.original_representative_id || "", role: "seller", percentage: "100" }]); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [saleId, revision]);
  useEffect(() => {
    const controller = new AbortController();
    if (canManage) void apiClient.request<Coverage[]>("/api/v1/sales/commission-coverages", { signal: controller.signal }).then(rows => { if (!controller.signal.aborted) setCoverages(rows); }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [canManage, revision]);
  async function write(path: string, payload: unknown, method: "POST" | "PUT", message: string) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try { await apiClient.request(path, { method, headers: { "Idempotency-Key": key }, body }); keys.current.delete(signature); setNotice(message); setRevision(value => value + 1); }
    catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  async function saveShares(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!participation) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await write(`/api/v1/sales/${saleId}/commission-participation`, { expected_sale_version: participation.sale_version, participants: shares.map(row => ({ representative_id: row.representative_id, role: row.role, percentage: row.percentage })), reason: values.reason }, "PUT", "Participación acordada. Se conservará al confirmar la venta, junto con la política efectiva.");
  }
  async function saveCoverage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    await write("/api/v1/sales/commission-coverages", values, "POST", "Reemplazo temporal registrado. Las ventas ya confirmadas conservan su autoría y sus participantes.");
  }
  const name = (id: string) => reps.find(rep => rep.rep_id === id)?.full_name || id.slice(0, 8);
  return <section className="team-panel"><h2 className="team-panel-title"><UsersRound size={20} aria-hidden="true" />Venta compartida y reemplazos temporales</h2><div className="mt-4 space-y-4"><p className="team-note">La participación se acuerda antes de confirmar una venta y suma exactamente 100 %. Los reemplazos afectan nuevas confirmaciones dentro de sus fechas y no modifican ventas anteriores ni cambian la autoría de la cartera.</p>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    {canManage && <div className="team-switch" aria-label="Tipo de asignación"><button type="button" className={button} aria-pressed={tab === "shares"} onClick={() => setTab("shares")}>Ventas compartidas</button><button type="button" className={button} aria-pressed={tab === "replacements"} onClick={() => setTab("replacements")}>Reemplazos temporales</button></div>}
    <div hidden={tab !== "shares"} className="space-y-4"><RemoteEntitySelect<Sale> value={saleId} onChange={value => { setSaleId(value); setParticipation(null); }} endpoint="/api/v1/sales/commission-sale-options" entityType="sale" mapOption={row => ({ value: row.sale_id || row.id || "", label: row.document_number || `${row.series || "Venta"}-${row.number || ""}`, data: row })} label="Venta para consultar o acordar participación" disabled={busy} />
    {participation && <form className="team-editor space-y-4" key={`${participation.sale_id}:${participation.sale_version}`} onSubmit={saveShares}><h3 className="font-semibold">{participation.document_number} · {participation.status} · Versión {participation.sale_version}</h3><p className="text-sm">Autor: {participation.original_representative_id ? name(participation.original_representative_id) : "Sin vendedor asignado"} · {participation.frozen ? `Política ${participation.policy?.version} conservada al vender` : "Participación pendiente de confirmación"}</p>{shares.map((row, index) => <div className="grid gap-2 md:grid-cols-4" key={index}><label className="grid gap-1 text-sm">Participante<CustomSelect remote={{ resource: "sales_reps" }} searchable={true} className={field} value={row.representative_id} required disabled={busy || participation.status !== "draft"} onChange={event => setShares(previous => previous.map((item, position) => position === index ? { ...item, representative_id: event.target.value } : item))}><option value="">Seleccione vendedor</option>{row.representative_id && !reps.some(rep => rep.rep_id === row.representative_id) && <option value={row.representative_id}>{row.name || name(row.representative_id)}</option>}{reps.map(rep => <option key={rep.rep_id} value={rep.rep_id}>{rep.full_name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Función<CustomSelect searchable={false} className={field} value={row.role} disabled={busy || participation.status !== "draft"} onChange={event => setShares(previous => previous.map((item, position) => position === index ? { ...item, role: event.target.value } : item))}><option value="seller">Vendedor</option><option value="prospector">Captador</option><option value="team">Equipo</option><option value="replacement">Reemplazo</option></CustomSelect></label><label className="grid gap-1 text-sm">Participación %<input className={field} type="number" min="0.000001" max="100" step="0.000001" required value={row.percentage} disabled={busy || participation.status !== "draft"} onChange={event => setShares(previous => previous.map((item, position) => position === index ? { ...item, percentage: event.target.value } : item))} /></label>{participation.status === "draft" && <button type="button" className={button} disabled={busy || shares.length <= 1} onClick={() => setShares(previous => previous.filter((_, position) => position !== index))}>Quitar participante</button>}</div>)}{participation.status === "draft" && <><button type="button" className={button} disabled={busy || shares.length >= 20} onClick={() => setShares(previous => [...previous, { representative_id: "", role: "team", percentage: "0" }])}>Agregar participante</button><label className="grid gap-1 text-sm">Motivo del acuerdo<input className={field} name="reason" required minLength={5} maxLength={2000} disabled={busy} /></label><button className={`${button} team-primary`} disabled={busy}>Guardar participación</button></>}</form>}
    </div>{canManage && <section hidden={tab !== "replacements"} className="team-editor space-y-4"><h3 className="font-semibold">Reemplazos por ausencia</h3><p className="text-xs text-slate-500">Si la venta tiene un reparto explícito, prevalece ese acuerdo. En caso contrario se aplica un solo reemplazo del vendedor autor; no se encadenan reemplazos. El porcentaje restante conserva al autor original.</p><form className="space-y-3" onSubmit={saveCoverage}><div className="grid gap-3 md:grid-cols-3"><label className="grid gap-1 text-sm">Vendedor ausente<CustomSelect remote={{ resource: "sales_reps" }} searchable={true} className={field} name="representative_id" required disabled={busy}><option value="">Seleccione vendedor</option>{reps.map(rep => <option key={rep.rep_id} value={rep.rep_id}>{rep.full_name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Reemplazo<CustomSelect remote={{ resource: "sales_reps" }} searchable={true} className={field} name="replacement_id" required disabled={busy}><option value="">Seleccione reemplazo</option>{reps.map(rep => <option key={rep.rep_id} value={rep.rep_id}>{rep.full_name}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Porcentaje para reemplazo<input className={field} name="percentage" type="number" min="0.000001" max="100" step="0.000001" required disabled={busy} /></label><label className="grid gap-1 text-sm">Desde<input className={field} name="starts_on" type="date" required disabled={busy} /></label><label className="grid gap-1 text-sm">Hasta<input className={field} name="ends_on" type="date" required disabled={busy} /></label><label className="grid gap-1 text-sm">Motivo<input className={field} name="reason" required minLength={5} maxLength={2000} disabled={busy} /></label></div><button className={`${button} team-primary`} disabled={busy}>Registrar reemplazo</button></form>{coverages.map(row => <article className="space-y-2 rounded-lg border p-3 text-sm" key={row.id}><p><strong>{name(row.representative_id)} → {name(row.replacement_id)}</strong> · {row.percentage} % · {row.status}</p><p>{row.starts_on} a {row.ends_on} · {row.reason} · Versión {row.version}</p>{row.status === "active" && <form className="flex gap-2" onSubmit={event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); void write("/api/v1/sales/commission-coverages", { ...row, identifier: row.id, expected_version: row.version, reason: values.reason, status: "cancelled" }, "POST", "Reemplazo cancelado para nuevas confirmaciones. La participación histórica se conserva."); }}><input aria-label="Motivo de cancelación del reemplazo" className={field} name="reason" required minLength={5} maxLength={2000} placeholder="Motivo de cancelación" disabled={busy} /><button className={button} disabled={busy}>Cancelar reemplazo</button></form>}</article>)}</section>}
  </div></section>;
}
