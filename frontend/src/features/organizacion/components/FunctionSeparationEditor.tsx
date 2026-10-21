import "./operating-profile.css";
import "./function-separation.css";
import { ShieldCheck, LockKeyhole, History as HistoryIcon, Save, X } from "lucide-react";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Policy = { version: number; enabled: Record<string, boolean>; processes: Record<string, { label: string; mandatory: boolean }>; definition: string };
type Event = { version: number; enabled: Record<string, boolean>; reason: string; actor: string; at: string };
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : "No se pudo consultar o guardar la separación de funciones."; }

export function FunctionSeparationEditor({ canWrite }: { canWrite: boolean }) {
  const historyTitle = useId();
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRevision, setHistoryRevision] = useState(0);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [history, setHistory] = useState<Event[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyPage, setHistoryPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => { const controller = new AbortController(); void apiClient.request<Policy>("/api/v1/business/function-separation", { signal: controller.signal }).then(row => { if (!controller.signal.aborted) { setPolicy(row); setEnabled(row.enabled); } }).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); }); return () => controller.abort(); }, [revision]);
  useEffect(() => {
    if (!historyOpen) return;
    const controller = new AbortController(); setHistoryLoading(true); setHistoryError("");
    void apiClient.request<Event[]>(`/api/v1/business/function-separation/history?limit=20&offset=${historyPage * 20}`, { signal: controller.signal }).then(rows => { if (!controller.signal.aborted) setHistory(rows); }).catch(cause => { if (!controller.signal.aborted) setHistoryError(problem(cause)); }).finally(() => { if (!controller.signal.aborted) setHistoryLoading(false); });
    return () => controller.abort();
  }, [historyOpen, historyPage, revision, historyRevision]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!policy || lock.current || !canWrite) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const body = JSON.stringify({ expected_version: policy.version, enabled, reason: values.reason }); const key = keys.current.get(body) || crypto.randomUUID(); keys.current.set(body, key);
    lock.current = true; setBusy(true); setError(""); setNotice("");
    try { await apiClient.request("/api/v1/business/function-separation", { method: "PUT", headers: { "Idempotency-Key": key }, body }); setNotice("Reglas guardadas. Las próximas revisiones dejarán constancia de la versión aplicada."); setRevision(value => value + 1); }
    catch (cause) { setError(problem(cause)); }
    finally { lock.current = false; setBusy(false); }
  }
  return <section className="operating-profile function-separation"><div className="space-y-5">
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{!policy && !error && <p role="status">Cargando reglas de revisión…</p>}
    {policy && <form className="space-y-5" onSubmit={submit}><p className="operating-profile-note"><ShieldCheck size={18} aria-hidden="true" />{policy.definition}</p>
      {[false, true].map(mandatory => <section className="space-y-3" key={String(mandatory)} aria-label={mandatory ? "Protecciones obligatorias" : "Reglas configurables"}><div className="operating-profile-area-heading"><h3>{mandatory ? "Protecciones obligatorias" : "Reglas configurables"}</h3>{mandatory && <span className="function-separation-lock"><LockKeyhole size={14} aria-hidden="true" />Siempre activas</span>}</div><p className="function-separation-description">{mandatory ? "Estas protecciones se mantienen activas y no se pueden deshabilitar." : "Activar una regla exige una revisión independiente para esa operación."}</p><fieldset className="grid gap-3 md:grid-cols-2" disabled={!canWrite || busy}>{Object.entries(policy.processes).filter(([, process]) => process.mandatory === mandatory).map(([key, process]) => <article className={`operating-profile-area ${mandatory || (enabled[key] ?? true) ? "is-enabled" : ""}`} key={key}><label className="operating-profile-area-label"><input type="checkbox" role="switch" aria-label={process.label} checked={mandatory || (enabled[key] ?? true)} disabled={mandatory || !canWrite || busy} onChange={event => setEnabled(previous => ({ ...previous, [key]: event.target.checked }))} /><span><strong>{process.label}</strong><small>{mandatory ? "Siempre requiere otra persona autorizada." : (enabled[key] ?? true) ? "Se exige una persona distinta del autor o solicitante." : "Sin esta restricción adicional; se mantienen los permisos habituales."}</small></span></label><InfoTooltip title={process.label} description={mandatory ? "Protección obligatoria. La revisión debe hacerla otra persona autorizada; no puede desactivarse desde la configuración." : "Al activar esta regla, el autor o solicitante no puede resolver la revisión de su propia operación. El cambio se aplica a decisiones futuras después de guardar y conserva las decisiones anteriores."} interactive align="right" /></article>)}</fieldset></section>)}
      <p className="function-separation-description">Si el documento no identifica a su autor, una regla activa bloquea la decisión hasta resolver su origen. Los cambios se registran con su motivo.</p>
      {canWrite && <><div className="operating-profile-reason"><div className="operating-profile-label"><label htmlFor={`${historyTitle}-reason`}>Motivo del cambio</label><InfoTooltip title="Motivo del cambio" description="Explica por qué modificas las reglas de revisión. Requiere al menos 5 caracteres y queda guardado en el historial de esta versión." interactive /></div><textarea id={`${historyTitle}-reason`} name="reason" minLength={5} maxLength={2000} required disabled={busy} /></div><button className={`${button} operating-profile-primary`} disabled={busy}><Save size={16} aria-hidden="true" />{busy ? "Guardando…" : "Guardar reglas de revisión"}</button></>}
    </form>}
    <div className="function-separation-history-action"><button type="button" className={button} disabled={busy} aria-haspopup="dialog" onClick={() => { setHistoryPage(0); setHistoryOpen(true); }}><HistoryIcon size={16} aria-hidden="true" />Historial de reglas</button></div>
    {historyOpen && <ModalSurface labelledBy={historyTitle} onClose={() => setHistoryOpen(false)} className="function-separation-modal"><section className="function-separation-dialog"><header><h2 id={historyTitle}>Historial de reglas</h2><button type="button" className={button} aria-label="Cerrar historial de reglas" onClick={() => setHistoryOpen(false)}><X size={18} /></button></header><div className="function-separation-history-body">{historyLoading ? <p role="status">Cargando historial…</p> : historyError ? <div role="alert"><p>{historyError}</p><button type="button" className={button} onClick={() => setHistoryRevision(value => value + 1)}>Reintentar</button></div> : history.length === 0 ? <p className="function-separation-description">No hay versiones guardadas en esta página.</p> : history.map(row => <article className="rounded border p-3 text-sm space-y-2" key={row.version}><strong>Versión {row.version} · {row.actor}</strong><p>{new Date(row.at).toLocaleString("es-PE")} · {row.reason}</p><details><summary className="cursor-pointer text-xs">Reglas opcionales de esta versión</summary>{Object.entries(row.enabled).filter(([key]) => !policy?.processes[key]?.mandatory).map(([key, active]) => <p className="text-xs" key={key}>{policy?.processes[key]?.label || key}: {active ? "Revisión independiente exigida" : "Sin esta restricción adicional"}</p>)}</details></article>)}</div><footer><span>Página {historyPage + 1}</span><div><button type="button" className={button} disabled={historyLoading || Boolean(historyError) || historyPage === 0} onClick={() => setHistoryPage(value => value - 1)}>Anterior</button><button type="button" className={button} disabled={historyLoading || Boolean(historyError) || history.length < 20} onClick={() => setHistoryPage(value => value + 1)}>Siguiente</button></div></footer></section></ModalSurface>}
  </div></section>;
}
