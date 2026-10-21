import { Save, History, ChevronDown, X } from "lucide-react";
import "./return-policy.css";
import { cloneElement, useEffect, useId, useRef, useState, type FormEvent, type ReactElement } from "react";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { apiClient } from "../../../api/client";

type Rule = { returnable: boolean; days: number; allowed_conditions: string[]; allowed_packaging: string[]; evidence_required: boolean; allow_exceptions: boolean; retention_percentage: string; retention_description: string };
type Policy = { version: number; default_rule: Rule; rules: Record<string, Rule>; reason: string; actor?: string; at?: string; can_manage?: boolean };
const types: Record<string, string> = { product: "Productos", service: "Servicios", kit: "Kits" };
const conditions: Record<string, string> = { unused: "Sin uso", used: "Usado", damaged: "Dañado", not_applicable: "No aplica" };
const packaging: Record<string, string> = { sealed: "Sellado", opened: "Abierto", missing: "Sin empaque", not_applicable: "No aplica" };
const field = "rounded-lg border border-slate-300 bg-white p-2 text-sm";

export function ReturnPolicyPanel({ standalone = false, canWrite = true }: { standalone?: boolean; canWrite?: boolean } = {}) {
  const formId = useId();
  const [baseline, setBaseline] = useState("");
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyAttempt, setHistoryAttempt] = useState(0);
  const [history, setHistory] = useState<Policy[]>([]);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  useEffect(() => {
    const controller = new AbortController();
    void apiClient.request<Policy>("/api/v1/return-policy", { signal: controller.signal }).then(value => { if (!controller.signal.aborted) { setPolicy(value); setBaseline(policySnapshot(value)); setCanManage(Boolean(value.can_manage)); } }).catch(cause => { if (!controller.signal.aborted) setError(detail(cause)); });
    return () => controller.abort();
  }, []);
  function detail(cause: unknown) { const value = (cause as { detail?: unknown })?.detail; return typeof value === "string" ? value : Array.isArray(value) ? value.map(item => String((item as { msg?: string }).msg || "Revise los datos")).join("; ") : "No se pudo obtener o guardar la política."; }
  function changeRule(key: string, changes: Partial<Rule>) {
    setPolicy(previous => !previous ? previous : key === "default" ? { ...previous, default_rule: { ...previous.default_rule, ...changes } } : { ...previous, rules: { ...previous.rules, [key]: { ...previous.rules[key], ...changes } } });
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!policy || !canManage || !canWrite || !dirty || lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify({ version: policy.version, default_rule: policy.default_rule, rules: policy.rules, reason });
    const key = keys.current.get(body) || crypto.randomUUID();
    keys.current.set(body, key);
    try { const result = await apiClient.request<Policy>("/api/v1/return-policy", { method: "PUT", headers: { "Idempotency-Key": key }, body }); setPolicy(result); setBaseline(policySnapshot(result)); setReason(""); setHistory([]); keys.current.delete(body); setNotice("Política guardada. Se aplicará a nuevas confirmaciones de venta; las condiciones históricas se conservan."); }
    catch (cause) { setError(detail(cause)); }
    finally { setBusy(false); lock.current = false; }
  }
  useEffect(() => {
    if (!historyOpen) return;
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError("");
    setHistory([]);
    void apiClient.request<Policy[]>("/api/v1/return-policy/history", { signal: controller.signal }).then(result => {
      if (!controller.signal.aborted) setHistory(result);
    }).catch(cause => {
      if (!controller.signal.aborted) setHistoryError(detail(cause));
    }).finally(() => {
      if (!controller.signal.aborted) setHistoryLoading(false);
    });
    return () => controller.abort();
  }, [historyOpen, historyAttempt]);
  const editable = canManage && canWrite;
  const dirty = Boolean(policy && baseline && policySnapshot(policy) !== baseline);
  const summary = (rule: Rule) => !rule.returnable ? "no admite devolución comercial" : `${rule.days} días, ${Number(rule.retention_percentage) > 0 ? `retención del ${Number(rule.retention_percentage)} %` : "sin retención"}`;
  const Root = standalone ? "section" : "details";
  return <Root className={`return-policy-workspace space-y-5 ${editable ? "return-policy-with-savebar" : ""}`}>
    {!standalone && <summary className="font-semibold">Políticas de devolución</summary>}
    <div className="return-policy-topline"><h2>Reglas de devolución</h2>{canManage && <button type="button" className="return-policy-secondary" disabled={busy} onClick={() => setHistoryOpen(true)}><History size={17} aria-hidden="true" />Consultar historial</button>}</div>
    {error && <p role="alert" className="return-policy-alert">{error}</p>}{notice && <p role="status" className="return-policy-notice">{notice}</p>}
    {!policy && !error && <p role="status" className="return-policy-card">Cargando políticas de devolución…</p>}
    {policy && <form id={formId} onSubmit={save} className="space-y-6">
      {!editable && <p className="text-sm text-slate-500">Modo de consulta. La edición requiere permiso de administración y operaciones habilitadas.</p>}
      <section aria-label="Regla general" className="return-policy-card space-y-5"><div className="return-policy-label"><h3 className="font-semibold">Regla general</h3><Help title="Regla general" description="Se aplica a todos los artículos que no tengan condiciones propias activadas. Cada venta conserva la política vigente cuando se confirma." /></div><RuleFields rule={policy.default_rule} disabled={!editable || busy} onChange={changes => changeRule("default", changes)} /></section>
      <section aria-labelledby={`${formId}-exceptions`} className="return-policy-exceptions space-y-4">
        <div className="return-policy-exceptions-heading"><div className="return-policy-label"><h3 id={`${formId}-exceptions`}>Excepciones por tipo</h3><Help title="Excepciones por tipo" description="Permiten configurar condiciones distintas para productos, servicios o kits. Al activar un tipo se copian los valores generales actuales; después se editan de forma independiente. Al desactivarlo vuelve a usar la regla general." /></div><p>Solo activa estas opciones si Productos, Servicios o Kits se comportan distinto a la regla general.</p></div>
        {Object.entries(types).map(([key, label]) => {
          const custom = policy.rules[key];
          return <section key={key} aria-label={`Condiciones de ${label.toLowerCase()}`} className="return-policy-card space-y-4">
            <div className="return-policy-exception-heading"><div><div className="return-policy-label"><h4>{label}</h4><Help title={`Condiciones de ${label.toLowerCase()}`} description={`Activa el interruptor para personalizar las devoluciones de ${label.toLowerCase()}. Mientras esté apagado se usa la regla general.${key === "service" ? " Los servicios no requieren configurar empaque." : ""}`} /></div><p>{custom ? `Condiciones propias: ${summary(custom)}.` : `Usa la regla general: ${summary(policy.default_rule)}.`}</p></div><PolicySwitch label={`Usar condiciones propias para ${label.toLowerCase()}`} checked={Boolean(custom)} disabled={!editable || busy} controls={`${formId}-rule-${key}`} onChange={checked => setPolicy(previous => {
              if (!previous) return previous;
              const rules = { ...previous.rules };
              if (checked) rules[key] = { ...previous.default_rule, allowed_conditions: [...previous.default_rule.allowed_conditions], allowed_packaging: [...previous.default_rule.allowed_packaging] };
              else delete rules[key];
              return { ...previous, rules };
            })} /></div>
            {custom && <div id={`${formId}-rule-${key}`} className="return-policy-exception-fields"><RuleFields rule={custom} service={key === "service"} disabled={!editable || busy} onChange={changes => changeRule(key, changes)} /></div>}
          </section>;
        })}
      </section>
    </form>}
    {policy && editable && <div className="return-policy-savebar">
      {dirty && <PolicyField label="Motivo del cambio" description="Explica por qué modificas las condiciones. Se guarda en el historial de la nueva versión y requiere al menos 5 caracteres."><textarea form={formId} value={reason} required minLength={5} maxLength={2000} rows={2} placeholder="Explica el motivo de esta nueva versión" className={field} disabled={busy} onChange={event => setReason(event.target.value)} /></PolicyField>}
      <div className="return-policy-savebar-actions"><span role="status">{dirty ? "Cambios pendientes de guardar" : "Sin cambios pendientes"}</span><button type="submit" form={formId} className="return-policy-primary" disabled={busy || !dirty}><Save size={17} aria-hidden="true" />{busy ? "Guardando…" : "Guardar nueva versión"}</button></div>
    </div>}
    {historyOpen && <ModalSurface labelledBy={`${formId}-history-title`} onClose={() => setHistoryOpen(false)} className="return-policy-history-modal">
      <section className="return-policy-history-dialog">
        <header className="return-policy-history-header"><div><h2 id={`${formId}-history-title`}>Historial de versiones</h2><p>Consulta quién cambió las condiciones y el motivo de cada versión.</p></div><button type="button" className="return-policy-secondary" aria-label="Cerrar historial" onClick={() => setHistoryOpen(false)}><X size={18} aria-hidden="true" /></button></header>
        <div className="return-policy-history-body" aria-busy={historyLoading}>
          {historyLoading ? <p role="status">Cargando historial…</p> : historyError ? <div role="alert" className="space-y-3"><p className="return-policy-alert">No se pudo cargar el historial. {historyError}</p><button type="button" className="return-policy-secondary" onClick={() => setHistoryAttempt(value => value + 1)}>Reintentar</button></div> : history.length === 0 ? <div className="return-policy-history-empty"><History size={28} aria-hidden="true" /><h3>Aún no hay versiones guardadas</h3><p>La política inicial no genera un registro. Al guardar una nueva versión aparecerá aquí con su motivo, fecha y responsable.</p></div> : history.map(item => <details key={item.version} className="return-policy-history"><summary>Versión {item.version}</summary><p>{item.actor || "Responsable no registrado"} · {item.at ? new Date(item.at).toLocaleString("es-PE") : "Fecha no registrada"}</p><p><strong>Motivo:</strong> {item.reason || "Sin motivo registrado"}</p><HistoryRule label="Regla general" rule={item.default_rule} />{Object.entries(item.rules).map(([key, rule]) => <HistoryRule key={key} label={types[key] || key} rule={rule} service={key === "service"} />)}</details>)}
        </div>
        <footer className="return-policy-history-footer"><button type="button" className="return-policy-secondary" onClick={() => setHistoryOpen(false)}>Cerrar</button></footer>
      </section>
    </ModalSurface>}

  </Root>;
}

function policySnapshot(policy: Policy) {
  return JSON.stringify({ default_rule: policy.default_rule, rules: policy.rules });
}

function RuleFields({ rule, disabled, onChange, service = false }: { rule: Rule; disabled: boolean; onChange: (changes: Partial<Rule>) => void; service?: boolean }) {
  return <fieldset className="space-y-5" disabled={disabled}>
    <div className="return-policy-master"><PolicySwitch help="Permite devoluciones comerciales bajo estas condiciones. Al desactivarlo se ocultan los campos y se conservan sus valores; no cambia las condiciones de ventas ya confirmadas." label="Admite devolución comercial" checked={rule.returnable} disabled={disabled} onChange={checked => onChange({ returnable: checked })} /><p>{rule.returnable ? "Configura las condiciones que deben cumplir las devoluciones." : "No se admite devolución comercial con esta regla. Las condiciones se conservan para cuando vuelva a activarse."}</p></div>
    {rule.returnable && <>
      <PolicyField label="Plazo desde la venta (días calendario)" description="Máximo de días calendario desde la fecha de venta para admitir la devolución. Incluye fines de semana y feriados. Un plazo de 0 permite únicamente el mismo día." className="return-policy-days"><input className={field} type="number" min="0" max="3650" step="1" required value={rule.days} onChange={event => onChange({ days: Math.min(3650, Math.max(0, Math.floor(Number(event.target.value) || 0))) })} /></PolicyField>
      <div className={`grid gap-5 ${service ? "" : "lg:grid-cols-2"}`}>{[{ name: "Estado del artículo permitido", key: "allowed_conditions" as const, options: conditions }, ...(!service ? [{ name: "Empaque permitido", key: "allowed_packaging" as const, options: packaging }] : [])].map(group => <section key={group.key} className="return-policy-group"><div className="return-policy-label return-policy-group-title"><h3>{group.name}</h3><Help title={group.name} description={group.key === "allowed_conditions" ? "Selecciona los estados del artículo que aceptas al devolverlo. Puedes permitir varios. No aplica es excluyente: úsalo cuando no corresponda evaluar el estado. Debe quedar al menos una opción." : "Selecciona las condiciones de empaque aceptadas. Puedes permitir varias. Sin empaque significa que se permite devolver sin embalaje; No aplica indica que no corresponde evaluarlo y excluye las demás opciones."} /></div><div className="return-policy-chips" role="group" aria-label={group.name}>{Object.entries(group.options).map(([option, label]) => <button type="button" key={option} aria-pressed={rule[group.key].includes(option)} disabled={disabled} onClick={() => {
        const selected = rule[group.key];
        const next = option === "not_applicable" ? [option] : selected.includes(option) ? selected.filter(item => item !== option && item !== "not_applicable") : [...selected.filter(item => item !== "not_applicable"), option];
        if (next.length) onChange({ [group.key]: next });
      }} className="return-policy-chip">{label}</button>)}</div></section>)}</div>
      <section className="return-policy-retention space-y-4"><h3 className="text-sm font-semibold">Retención</h3><div className="grid gap-4 md:grid-cols-2"><PolicyField label="Retención del valor devuelto (%)" description="Porcentaje que se descuenta del valor devuelto antes de aplicarlo a deuda, cambio, saldo a favor o reembolso. Usa 0 si no hay descuento."><input className={field} type="number" min="0" max="99.9999" step="0.0001" required value={rule.retention_percentage} onChange={event => onChange({ retention_percentage: event.target.value })} /></PolicyField>{Number(rule.retention_percentage) > 0 && <PolicyField label="Concepto de la retención" description="Describe el motivo del descuento. Es obligatorio cuando la retención es mayor que 0 y debe tener al menos 5 caracteres."><input className={field} required minLength={5} maxLength={255} value={rule.retention_description} placeholder="Motivo de la retención" onChange={event => onChange({ retention_description: event.target.value })} /></PolicyField>}</div></section>
      <section className="space-y-3"><h3 className="text-sm font-semibold">Requisitos y autorizaciones</h3><div className="grid gap-4 md:grid-cols-2"><PolicySwitch help="Exige registrar sustento documentado de la devolución. Una excepción autorizada no elimina la obligación de presentar esta evidencia." label="Requiere evidencia documentada" checked={rule.evidence_required} disabled={disabled} onChange={checked => onChange({ evidence_required: checked })} /><PolicySwitch help="Permite que una persona con permiso de aprobación autorice una excepción o exonere la retención con un motivo documentado. No omite la evidencia obligatoria ni las declaraciones requeridas." label="Admite excepción o exoneración autorizada" checked={rule.allow_exceptions} disabled={disabled} onChange={checked => onChange({ allow_exceptions: checked })} /></div></section>
    </>}
  </fieldset>;
}

function PolicySwitch({ label, checked, disabled, onChange, controls, help }: { label: string; checked: boolean; disabled: boolean; onChange: (checked: boolean) => void; controls?: string; help?: string }) {
  return <div className="return-policy-switch-help"><button type="button" role="switch" aria-checked={checked} aria-label={label} aria-controls={controls} disabled={disabled} onClick={() => onChange(!checked)} className="return-policy-switch"><span className="return-policy-switch-track" aria-hidden="true"><span /></span><span>{controls ? <ChevronDown size={17} aria-hidden="true" /> : label}</span></button>{help && <Help title={label} description={help} />}</div>;
}

function Help({ title, description }: { title: string; description: string }) {
  return <InfoTooltip title={title} description={description} interactive />;
}

function PolicyField({ label, description, children, className = "" }: { label: string; description: string; children: ReactElement<{ id?: string }>; className?: string }) {
  const id = useId();
  return <div className={`return-policy-field ${className}`}><div className="return-policy-label"><label htmlFor={id}>{label}</label><Help title={label} description={description} /></div>{cloneElement(children, { id })}</div>;
}

function HistoryRule({ label, rule, service = false }: { label: string; rule: Rule; service?: boolean }) {
  return <div className="return-policy-history-rule"><h3>{label}</h3><p>{rule.returnable ? `Admite devolución: ${rule.days} días calendario` : "No admite devolución comercial"}</p>{rule.returnable && <><p>Estado: {rule.allowed_conditions.map(value => conditions[value] || value).join(", ")}</p>{!service && <p>Empaque: {rule.allowed_packaging.map(value => packaging[value] || value).join(", ")}</p>}<p>Retención: {Number(rule.retention_percentage)} %{Number(rule.retention_percentage) > 0 ? ` · ${rule.retention_description}` : ""}</p><p>Evidencia requerida: {rule.evidence_required ? "Sí" : "No"} · Excepción autorizada: {rule.allow_exceptions ? "Sí" : "No"}</p></>}</div>;
}
