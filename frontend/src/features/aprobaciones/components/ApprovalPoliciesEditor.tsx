import { SettingLabel, SettingSwitch, SettingsHelp } from "../../../ui/components/SettingsControls";
import { selectorSeed } from "../../../api/selectorSeed";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Member = { id: string; name: string };
type Stage = { name: string; approver_ids: string[]; required_votes: number; due_hours: number };
type Policy = { id?: string; code: string; resource_type: string; action: string; metric: string; comparison: string; threshold: string; stages: Stage[]; is_active: boolean; version: number };
type Delegation = { id: string; principal_id: string; delegate_id: string; starts_at: string; ends_at: string; reason: string; status: string };
const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";
const button = "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:opacity-50";
const resources: Record<string, string> = { sale: "Venta", order: "Pedido", purchase_order: "Orden de compra", expense: "Gasto", return: "Devolución" };
const actions: Record<string, string> = { confirm: "Confirmar", approve: "Aprobar", accept: "Aceptar", submit: "Enviar a aprobación" };
const availableActions: Record<string, string[]> = { sale: ["confirm"], order: ["confirm", "approve"], purchase_order: ["approve"], expense: ["submit", "approve"], return: ["accept"] };
const initialStage = (): Stage => ({ name: "Revisión", approver_ids: [], required_votes: 1, due_hours: 48 });
const initialPolicy = (): Policy => ({ code: "", resource_type: "sale", action: "confirm", metric: "total_amount", comparison: "gt", threshold: "0", stages: [initialStage()], is_active: true, version: 0 });

export function ApprovalPoliciesEditor({ canWrite }: { canWrite: boolean }) {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [draft, setDraft] = useState<Policy>(initialPolicy);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());

  function problem(failure: unknown) { const detail = (failure as { detail?: unknown }).detail; return typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo completar la operación."; }
  async function load() {
    try {
      const [policyRows, memberRows, delegationRows] = await Promise.all([apiClient.request<Policy[]>("/api/v1/business/approval-policies"), selectorSeed<Member>("approvers", { active_only: "true" }), apiClient.request<Delegation[]>("/api/v1/business/approval-delegations")]);
      setPolicies(policyRows);
      setMembers(memberRows);
      setDelegations(delegationRows);
    } catch (failure) { setError(problem(failure)); }
  }
  useEffect(() => { if (canWrite) void load(); }, [canWrite]);
  async function write(path: string, body: unknown, method = "POST") {
    if (lock.current || !canWrite) return false;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const signature = JSON.stringify({ path, body, method });
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      await apiClient.request(path, { method, body: JSON.stringify(body), headers: { "Idempotency-Key": key } });
      keys.current.delete(signature);
      await load();
      setNotice("Configuración registrada.");
      return true;
    } catch (failure) { setError(problem(failure)); return false; }
    finally { lock.current = false; setBusy(false); }
  }
  async function savePolicy(event: FormEvent) {
    event.preventDefault();
    if (await write("/api/v1/business/approval-policies", draft, "PUT")) setDraft(initialPolicy());
  }
  async function delegate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form)) as Record<string, string>;
    const body = { ...values, starts_at: new Date(`${values.starts_at}:00-05:00`).toISOString(), ends_at: new Date(`${values.ends_at}:00-05:00`).toISOString() };
    if (await write("/api/v1/business/approval-delegations", body)) form.reset();
  }
  function changeStage(index: number, update: Partial<Stage>) { setDraft(current => ({ ...current, stages: current.stages.map((stage, position) => position === index ? { ...stage, ...update } : stage) })); }
  if (!canWrite) return null;
  return <section className="mt-6 space-y-5 rounded-2xl border border-slate-200 bg-white p-6 text-slate-900 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div><div className="settings-section-heading"><h2 className="text-lg font-semibold">Aprobaciones por condición y delegaciones</h2><SettingsHelp title="Aprobaciones por condición y delegaciones" description="Define qué acciones requieren autorización, quiénes pueden aprobarlas y cómo se delega temporalmente esa responsabilidad." /></div><p className="mt-1 text-sm text-slate-500">Las políticas bloquean la acción hasta reunir las decisiones de todas sus etapas sobre el documento vigente.</p></div><button type="button" className={button} disabled={busy} onClick={() => void load()}>Actualizar</button></div>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-700">{notice}</p>}
    <div className="grid items-start gap-5 xl:grid-cols-[1.4fr_1fr]"><form onSubmit={savePolicy} className="space-y-4 rounded-xl border p-4"><h3 className="font-medium">{draft.version ? `Editar ${draft.code} · versión ${draft.version}` : "Nueva política"}</h3><div className="grid gap-3 sm:grid-cols-2"><SettingLabel className="text-sm">Código<input className={input} required pattern="[A-Za-z][A-Za-z0-9_-]{0,63}" readOnly={draft.version > 0} value={draft.code} onChange={event => setDraft(current => ({ ...current, code: event.target.value }))} /></SettingLabel><SettingLabel className="text-sm">Documento<CustomSelect className={input} value={draft.resource_type} onChange={event => setDraft(current => ({ ...current, resource_type: event.target.value, action: availableActions[event.target.value][0], metric: "total_amount" }))}>{Object.entries(resources).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</CustomSelect></SettingLabel><SettingLabel className="text-sm">Acción protegida<CustomSelect className={input} value={draft.action} onChange={event => setDraft(current => ({ ...current, action: event.target.value }))}>{availableActions[draft.resource_type].map(key => <option key={key} value={key}>{actions[key]}</option>)}</CustomSelect></SettingLabel><SettingLabel className="text-sm">Condición<CustomSelect className={input} value={draft.metric} onChange={event => setDraft(current => ({ ...current, metric: event.target.value }))}><option value="always">Siempre</option><option value="total_amount">Importe total en moneda del documento</option>{["sale", "order"].includes(draft.resource_type) && <><option value="discount_percentage">Mayor descuento de una línea %</option><option value="margin_percentage">Margen sobre subtotal %</option></>}</CustomSelect></SettingLabel>{draft.metric !== "always" && <><SettingLabel className="text-sm">Comparación<CustomSelect className={input} value={draft.comparison} onChange={event => setDraft(current => ({ ...current, comparison: event.target.value }))}><option value="gt">Mayor que</option><option value="gte">Mayor o igual que</option><option value="lt">Menor que</option><option value="lte">Menor o igual que</option></CustomSelect></SettingLabel><SettingLabel className="text-sm">Umbral<input className={input} type="number" step="0.000001" min="0" required value={draft.threshold} onChange={event => setDraft(current => ({ ...current, threshold: event.target.value }))} /></SettingLabel></>}</div>
      {draft.stages.map((stage, index) => <fieldset key={index} className="space-y-3 rounded-lg border p-3"><legend className="px-2 text-sm font-medium">Etapa {index + 1}</legend><SettingLabel className="block text-sm">Nombre<input className={input} required minLength={2} maxLength={128} value={stage.name} onChange={event => changeStage(index, { name: event.target.value })} /></SettingLabel><SettingLabel className="block text-sm">Responsables autorizados<CustomSelect remote={{ resource: "approvers", active_only: true }} className={input} multiple required value={stage.approver_ids} onChange={event => changeStage(index, { approver_ids: Array.from(event.target.selectedOptions).map(option => option.value) })}>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect><span className="mt-1 block text-xs text-slate-500">Puedes seleccionar varias personas. El solicitante no puede aprobar su propia operación.</span></SettingLabel><div className="grid gap-3 sm:grid-cols-2"><SettingLabel className="text-sm">Decisiones favorables necesarias<input className={input} required type="number" min="1" max={Math.max(1, stage.approver_ids.length)} value={stage.required_votes} onChange={event => changeStage(index, { required_votes: Number(event.target.value) })} /></SettingLabel><SettingLabel className="text-sm">Plazo de etapa, horas<input className={input} required type="number" min="1" max="8760" value={stage.due_hours} onChange={event => changeStage(index, { due_hours: Number(event.target.value) })} /></SettingLabel></div><button type="button" className={button} disabled={draft.stages.length === 1 || busy} onClick={() => setDraft(current => ({ ...current, stages: current.stages.filter((_, position) => position !== index) }))}>Quitar etapa</button></fieldset>)}<div className="flex flex-wrap items-center gap-3"><button type="button" className={button} disabled={busy || draft.stages.length >= 10} onClick={() => setDraft(current => ({ ...current, stages: [...current.stages, initialStage()] }))}>Agregar etapa</button><SettingSwitch label="Política activa" description="Activa esta política de aprobación para las nuevas acciones que cumplan su condición. Los cambios se aplican al guardar una nueva versión." checked={draft.is_active} disabled={busy} onChange={event => setDraft(current => ({ ...current, is_active: event.target.checked }))} /></div><div className="flex gap-2"><button className={button} disabled={busy || !members.length}>Guardar política</button><button type="button" className={button} disabled={busy} onClick={() => setDraft(initialPolicy())}>Limpiar</button></div></form>
      <section className="space-y-3"><h3 className="font-medium">Políticas registradas</h3>{policies.length === 0 && <p className="text-sm text-slate-500">No hay políticas adicionales configuradas.</p>}{policies.map(policy => <button type="button" key={policy.id} className={`${button} block w-full text-left`} onClick={() => setDraft(structuredClone(policy))}><strong>{policy.code}</strong><span className="mt-1 block text-xs">{resources[policy.resource_type]} · {actions[policy.action]} · {policy.stages.length} etapas · {policy.is_active ? "Activa" : "Inactiva"} · v{policy.version}</span></button>)}<p className="text-xs text-slate-500">Un cambio crea una nueva versión de la política. Si cambia el documento aprobado, su autorización debe revisarse de nuevo.</p></section></div>
    <div className="grid gap-5 border-t pt-5 xl:grid-cols-2"><form onSubmit={delegate} className="space-y-3 rounded-xl border p-4"><h3 className="font-medium">Delegación temporal de aprobaciones</h3><SettingLabel className="block text-sm">Responsable titular<CustomSelect remote={{ resource: "approvers", active_only: true }} name="principal_id" className={input} required><option value="">Seleccionar</option>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect></SettingLabel><SettingLabel className="block text-sm">Reemplazo autorizado<CustomSelect remote={{ resource: "approvers", active_only: true }} name="delegate_id" className={input} required><option value="">Seleccionar</option>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect></SettingLabel><div className="grid gap-3 sm:grid-cols-2"><SettingLabel className="text-sm">Desde, hora de Lima<input className={input} name="starts_at" required type="datetime-local" /></SettingLabel><SettingLabel className="text-sm">Hasta, hora de Lima<input className={input} name="ends_at" required type="datetime-local" /></SettingLabel></div><SettingLabel className="block text-sm">Motivo<textarea className={input} name="reason" required minLength={3} maxLength={2000} /></SettingLabel><button className={button} disabled={busy}>Autorizar delegación</button></form><section className="space-y-3"><h3 className="font-medium">Delegaciones registradas</h3>{delegations.map(delegation => <div key={delegation.id} className="rounded-xl border p-4 text-sm"><strong>{members.find(member => member.id === delegation.principal_id)?.name || "Titular"} → {members.find(member => member.id === delegation.delegate_id)?.name || "Reemplazo"}</strong><p className="mt-1 text-xs">{new Date(delegation.starts_at).toLocaleString("es-PE", { timeZone: "America/Lima" })} a {new Date(delegation.ends_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</p><p className="mt-2">{delegation.reason}</p><p className="mt-1 text-xs">{({ active: "Vigente", scheduled: "Programada", expired: "Vencida", revoked: "Revocada" } as Record<string, string>)[delegation.status]}</p>{["active", "scheduled"].includes(delegation.status) && <button className={`${button} mt-2`} type="button" disabled={busy} onClick={() => void write(`/api/v1/business/approval-delegations/${delegation.id}/revoke`, {})}>Revocar</button>}</div>)}{!delegations.length && <p className="text-sm text-slate-500">No hay delegaciones registradas.</p>}</section></div>
  </section>;
}
