import { CustomSelect } from "../../../ui/components/CustomSelect";
import "./cash-submodules.css";
import "./cash-forecast.css";
import { TablePagination } from "../../../ui/components/TablePagination";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { ChartNoAxesCombined, Calculator, Save, X, ArrowDownLeft, ArrowUpRight, ChevronDown } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { apiClient } from "../../../api/client";

type Override = { source_key: string; fingerprint: string; included: boolean; due_date: string | null; point_key: string | null; amount: string | null };
type ManualEvent = { id: string; title: string; direction: "in" | "out" | "transfer"; currency: string; amount: string; due_date: string; point_key: string | null; destination_key: string | null };
type Config = { horizon_days: number; overrides: Override[]; manual_events: ManualEvent[] };
type Scenario = { id: string; version: number; name: string; reason: string; config: Config; created_at: string; created_by: string };
type Point = { key: string; name: string; currency: string; opening_balance: string; is_active: boolean };
type Source = { key: string; title: string; direction: string; kind: string; currency: string; source_amount?: string; amount: string; original_due_date: string; due_date: string; point_key: string | null; fixed_point: boolean; default_included: boolean; included: boolean; in_horizon: boolean; is_overdue: boolean; needs_review: boolean; note: string; fingerprint: string | null };
type Day = { date: string; opening: string; incoming: string; outgoing: string; closing: string; negative: boolean; requires_prior_receipts: boolean; source_keys: string[] };
type Timeline = { key: string; name: string; currency: string; opening_balance: string; closing_balance: string; first_negative_date: string | null; days: Day[] };
type Forecast = { business_date: string; end_date: string; points: Point[]; items: Source[]; timelines: Timeline[]; warnings: string[]; stale_source_keys: string[]; in_transit_by_currency: Record<string, string>; method: string; generated_at: string };
const input = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";
const freshConfig = (): Config => ({ horizon_days: 30, overrides: [], manual_events: [] });
const kinds: Record<string, string> = { receivable: "Cobros", payable: "Obligaciones de compra", purchase_invoice: "Facturas sin obligación", purchase_estimate: "Compras estimadas", expense: "Gastos aprobados", petty_cash: "Caja chica", cash_in_transit: "Efectivo en tránsito", manual: "Hipótesis manual", manual_transfer: "Traspaso simulado" };
function problem(cause: unknown) { const detail = (cause as { detail?: unknown })?.detail; return typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map(item => { const row = item as { loc?: (string | number)[]; msg?: string }; return `${row.loc?.join(".") || "Dato"}: ${row.msg || "Valor inválido"}`; }).join("; ") : cause instanceof Error ? cause.message : "No se pudo calcular la previsión."; }

export function CashForecastPanel({ canWrite, revision }: { canWrite: boolean; revision: number }) {
  const [config, setConfig] = useState<Config>(freshConfig);
  const configRef = useRef(config);
  configRef.current = config;
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [calculatedConfig, setCalculatedConfig] = useState("");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<Scenario | null>(null);
  const selectedRef = useRef(selected?.id);
  selectedRef.current = selected?.id;
  const [name, setName] = useState("");
  const [reason, setReason] = useState("");
  const [history, setHistory] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [timelineKey, setTimelineKey] = useState("");
  const [currency, setCurrency] = useState("");
  const [kind, setKind] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [dayPage, setDayPage] = useState(0);
  const [dayPageSize, setDayPageSize] = useState(10);
  const [activeTab, setActiveTab] = useState("daily");
  const [detailDay, setDetailDay] = useState<Day | null>(null);
  const [detailPage, setDetailPage] = useState(0);
  const [detailPageSize, setDetailPageSize] = useState(10);
  const panelId = useId();
  const requestId = useRef(0);
  const saving = useRef(false);
  const keys = useRef(new Map<string, string>());
  const dirty = calculatedConfig !== JSON.stringify(config);
  const timeline = forecast?.timelines.find(item => item.key === timelineKey) || forecast?.timelines.find(item => item.key.startsWith("currency:")) || forecast?.timelines[0];
  const currencies = [...new Set([...(forecast?.points.map(point => point.currency) || []), ...(forecast?.items.map(item => item.currency) || [])])].sort();
  const filtered = (forecast?.items || []).filter(item => (!currency || item.currency === currency) && (!kind || item.kind === kind));
  const sources = filtered.slice(page * pageSize, page * pageSize + pageSize);
  const detailSources = detailDay?.source_keys.map(key => forecast?.items.find(item => item.key === key) || { key, title: key, currency: timeline?.currency || "", amount: "", kind: "", direction: "" }) || [];
  const activePoints = (forecast?.points || []).filter(point => point.is_active);

  useEffect(() => {
    const controller = new AbortController();
    const identifier = ++requestId.current;
    const snapshot = JSON.stringify(configRef.current);
    setLoading(true);
    setError("");
    void Promise.all([
      apiClient.request<Forecast>("/api/v1/cash-forecast/preview", { method: "POST", body: snapshot, signal: controller.signal }),
      apiClient.request<Scenario[]>("/api/v1/cash-forecast/scenarios", { signal: controller.signal })
    ]).then(([result, saved]) => { if (controller.signal.aborted || identifier !== requestId.current) return; setForecast(result); setCalculatedConfig(snapshot); setScenarios(saved); setPage(0); setDayPage(0); setDetailDay(null); }).catch(cause => { if (!controller.signal.aborted && identifier === requestId.current) setError(problem(cause)); }).finally(() => { if (!controller.signal.aborted && identifier === requestId.current) setLoading(false); });
    return () => controller.abort();
  }, [revision, refresh]);

  function setRule(source: Source, changes: Partial<Override>) {
    if (!source.fingerprint) return;
    const fingerprint = source.fingerprint;
    setConfig(previous => {
      const existing = previous.overrides.find(rule => rule.source_key === source.key);
      const rule: Override = { source_key: source.key, fingerprint, included: existing?.included ?? source.default_included, due_date: existing?.due_date || null, point_key: existing?.point_key || source.point_key, amount: existing?.amount || null, ...changes };
      return { ...previous, overrides: [...previous.overrides.filter(item => item.source_key !== source.key), rule] };
    });
  }

  function loadScenario(value: Scenario | null) {
    setSelected(value);
    setConfig(value?.config || freshConfig());
    setName(value?.name || "");
    setReason("");
    setHistory([]);
    setPage(0);
    setRefresh(current => current + 1);
  }

  async function save(asCopy: boolean) {
    if (saving.current || !name.trim() || reason.trim().length < 5) return;
    saving.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const identifier = asCopy ? null : selected?.id;
    const path = `/api/v1/cash-forecast/scenarios${identifier ? `/${identifier}` : ""}`;
    const body = JSON.stringify({ ...config, name, reason, version: identifier ? selected?.version : 0 });
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      const result = await apiClient.request<Scenario>(path, { method: identifier ? "PUT" : "POST", body, headers: { "Idempotency-Key": key } });
      keys.current.delete(signature);
      setSelected(result);
      setConfig(result.config);
      setName(result.name);
      setReason("");
      setHistory([]);
      setNotice(`Escenario guardado como versión ${result.version}. No se registraron movimientos reales.`);
      setRefresh(current => current + 1);
    } catch (cause) { setError(problem(cause)); }
    finally { saving.current = false; setBusy(false); }
  }

  async function loadHistory() {
    if (!selected) return;
    const identifier = selected.id;
    try { const rows = await apiClient.request<Scenario[]>(`/api/v1/cash-forecast/scenarios/${identifier}/history`); if (selectedRef.current === identifier) setHistory(rows); }
    catch (cause) { setError(problem(cause)); }
  }

  function changeManual(identifier: string, changes: Partial<ManualEvent>) {
    setConfig(previous => ({ ...previous, manual_events: previous.manual_events.map(item => item.id === identifier ? { ...item, ...changes } : item) }));
  }

  return <section className="cash-submodule cash-submodule-forecast space-y-5">
    <div className="cash-submodule-toolbar flex flex-wrap items-center justify-between gap-4"><div><h2 className="font-semibold"><span className="cash-submodule-symbol"><ChartNoAxesCombined size={22} aria-hidden="true" /></span>Previsión de efectivo</h2><p className="text-sm text-slate-500">Saldos internos, compromisos y escenarios por fecha, moneda y punto de custodia.</p></div><button className={`${button} cash-button-primary`} disabled={loading || busy} onClick={() => setRefresh(value => value + 1)}><Calculator size={16} aria-hidden="true" />Calcular con datos actuales</button></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{loading && <p role="status" className="text-sm">Calculando previsión…</p>}{forecast && dirty && <p role="status" className="forecast-pending">Hay cambios pendientes de calcular. Los saldos y las alertas mostrados corresponden al cálculo anterior.</p>}
    <div className="forecast-controls"><label className="grid gap-1 text-sm">Escenario<CustomSelect className={input} disabled={busy || loading} value={selected?.id || ""} onChange={event => loadScenario(scenarios.find(item => item.id === event.target.value) || null)}><option value="">Escenario base sin guardar</option>{scenarios.map(item => <option key={item.id} value={item.id}>{item.name} · Versión {item.version}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Días desde hoy<input type="number" min="1" max="365" step="1" value={config.horizon_days} disabled={busy} onChange={event => { setConfig(previous => ({ ...previous, horizon_days: Math.min(365, Math.max(1, Math.floor(Number(event.target.value) || 1))) })); setPage(0); }} className={input} /></label>{selected && <button className={button} disabled={busy} onClick={() => void loadHistory()}>Consultar versiones anteriores</button>}</div>
    {canWrite && <details className="forecast-save"><summary><span><Save size={17} aria-hidden="true" />Guardar escenario</span><ChevronDown size={17} aria-hidden="true" /></summary><div className="forecast-save-fields grid gap-4 md:grid-cols-2"><label className="grid gap-1 text-sm">Nombre del escenario<input className={input} value={name} minLength={3} maxLength={128} disabled={busy} onChange={event => setName(event.target.value)} /></label><label className="grid gap-1 text-sm">Motivo del cambio<input className={input} value={reason} minLength={5} maxLength={2000} disabled={busy} onChange={event => setReason(event.target.value)} /></label><div className="flex flex-wrap gap-2"><button className={button} disabled={busy || loading || name.trim().length < 3 || reason.trim().length < 5} onClick={() => void save(false)}><Save size={16} aria-hidden="true" />Guardar {selected ? "nueva versión" : "escenario"}</button>{selected && <button className={button} disabled={busy || loading || name.trim().length < 3 || reason.trim().length < 5} onClick={() => void save(true)}>Guardar como otro escenario</button>}</div></div></details>}
    {history.length > 0 && <details open><summary className="cursor-pointer text-sm font-medium">Historial del escenario</summary>{history.map(item => <div key={item.version} className="mt-2 rounded-lg border p-3 text-sm"><p>Versión {item.version} · {item.name} · {item.created_at.slice(0, 19).replace("T", " ")}</p><p>{item.reason}</p><button className={button} disabled={busy} onClick={() => { setConfig(item.config); setRefresh(value => value + 1); setNotice(`Se cargaron las hipótesis de la versión ${item.version}. Guarde otra versión para conservar la recuperación.`); }}>Recuperar hipótesis de esta versión</button></div>)}</details>}
    {forecast && <><p className="text-xs text-slate-500">Desde {forecast.business_date} hasta {forecast.end_date}. Cálculo: {forecast.generated_at.slice(0, 19).replace("T", " ")}</p><details><summary className="cursor-pointer text-sm font-medium">Criterios de la previsión</summary><p className="mt-2 text-xs text-slate-600">{forecast.method}</p></details>
      {forecast.warnings.length > 0 && <details open><summary className="text-sm font-medium text-amber-900">Datos que requieren revisión ({forecast.warnings.length})</summary><ul className="list-disc pl-5 text-xs text-amber-900">{forecast.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details>}
      {Object.keys(forecast.in_transit_by_currency).length > 0 && <div className="flex flex-wrap gap-3">{Object.entries(forecast.in_transit_by_currency).map(([code, amount]) => <p key={code} className="rounded-lg bg-amber-50 p-3 text-sm">En tránsito, fuera del saldo inicial: {amount} {code}</p>)}</div>}
      <div className="grid gap-3 md:grid-cols-3">{forecast.timelines.filter(item => item.key.startsWith("currency:")).map(item => <article className="cash-forecast-summary rounded-lg border p-4 text-sm" key={item.key}><strong>{item.name.replace(new RegExp(` · ${item.currency}$`), "")} <span className="forecast-currency">{item.currency}</span></strong><div className="forecast-balance-pair"><div><span>Saldo inicial</span><p>{money(item.opening_balance, item.currency)}</p></div><div><span>Saldo proyectado</span><p className={Number(item.closing_balance) < 0 ? "forecast-negative" : "forecast-positive"}>{money(item.closing_balance, item.currency)}</p></div></div><p className={item.first_negative_date ? "text-red-700" : "text-slate-500"}>{item.first_negative_date ? `Primer saldo negativo: ${item.first_negative_date}` : "Sin saldo final diario negativo"}</p></article>)}</div>
      {forecast.timelines.some(item => !item.key.startsWith("currency:") && item.first_negative_date) && <div role="status" className="space-y-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-900"><strong>Compromisos que dejan puntos sin fondos o pendientes de asignar</strong>{forecast.timelines.filter(item => !item.key.startsWith("currency:") && item.first_negative_date).map(item => <p key={item.key}><button className="underline" onClick={() => { setTimelineKey(item.key); setDayPage(0); setActiveTab("daily"); }}>{item.name} · {item.currency} · Desde {item.first_negative_date}</button></p>)}</div>}
      <div role="tablist" aria-label="Secciones de proyección" className="forecast-tabs">{[["daily", "Proyección diaria"], ["documents", "Documentos e hipótesis"], ["manual", "Operaciones manuales"]].map(([key, label]) => <button type="button" key={key} role="tab" id={`${panelId}-tab-${key}`} aria-selected={activeTab === key} aria-controls={`${panelId}-panel-${key}`} tabIndex={activeTab === key ? 0 : -1} onKeyDown={event => {
        const tabs = ["daily", "documents", "manual"];
        const index = tabs.indexOf(activeTab);
        const next = event.key === "ArrowRight" ? tabs[(index + 1) % tabs.length] : event.key === "ArrowLeft" ? tabs[(index + 2) % tabs.length] : event.key === "Home" ? tabs[0] : event.key === "End" ? tabs[2] : null;
        if (next) { event.preventDefault(); setActiveTab(next); document.getElementById(`${panelId}-tab-${next}`)?.focus(); }
      }} onClick={() => setActiveTab(key)}>{label}</button>)}</div>
      {activeTab === "daily" && <section role="tabpanel" id={`${panelId}-panel-daily`} aria-labelledby={`${panelId}-tab-daily`} className="space-y-5">
        <div className="forecast-section-heading"><div><h3>Disponibilidad por día</h3><p>Revisa entradas, salidas y posibles faltas de fondos.</p></div><label className="grid gap-1 text-sm">Caja, fondo o consolidado<CustomSelect className={input} value={timeline?.key || ""} onChange={event => { setTimelineKey(event.target.value); setDayPage(0); }}>{forecast.timelines.map(item => <option key={item.key} value={item.key}>{item.name.endsWith(item.currency) ? item.name : `${item.name} · ${item.currency}`}{item.first_negative_date ? " · Falta de fondos" : ""}</option>)}</CustomSelect></label></div>
        {timeline ? <><div className="forecast-table-card"><table className="w-full text-left text-sm"><thead><tr><th>Fecha</th><th>Saldo inicial · {timeline.currency}</th><th>Entradas</th><th>Salidas</th><th>Saldo final</th><th>Compromisos y avisos</th></tr></thead><tbody>{timeline.days.slice(dayPage * dayPageSize, (dayPage + 1) * dayPageSize).map(day => <tr key={day.date}><td>{dateLabel(day.date)}</td><td className="forecast-number">{amount(day.opening)}</td><td className="forecast-number forecast-positive">{amount(day.incoming)}</td><td className="forecast-number forecast-outgoing">{amount(day.outgoing)}</td><td className={`forecast-number forecast-closing ${day.negative ? "forecast-negative" : ""}`}>{amount(day.closing)}</td><td><div className="forecast-day-actions">{day.negative ? <span className="forecast-badge forecast-badge-danger">Faltan fondos</span> : day.requires_prior_receipts ? <span className="forecast-badge forecast-badge-warning">Requiere ingresos previos</span> : null}{day.source_keys.length > 0 ? <button type="button" className="forecast-detail-button" aria-label={`Ver ${day.source_keys.length} compromisos del ${day.date}`} onClick={() => { setDetailDay(day); setDetailPage(0); }}>{day.source_keys.length} compromisos</button> : <span className="forecast-muted">Sin compromisos</span>}</div></td></tr>)}</tbody></table></div><TablePagination page={dayPage} pageSize={dayPageSize} total={timeline.days.length} loading={loading} onPageChange={setDayPage} onPageSizeChange={size => { setDayPageSize(size); setDayPage(0); }} /></> : <p className="forecast-empty">No hay saldos disponibles para proyectar.</p>}
      </section>}
      {activeTab === "documents" && <section role="tabpanel" id={`${panelId}-panel-documents`} aria-labelledby={`${panelId}-tab-documents`} className="space-y-5">
      <div className="forecast-section-heading"><div><h3>Documentos e hipótesis del cálculo</h3><p>Abre un documento para ajustar su inclusión, fecha, importe o destino.</p></div><div className="flex flex-wrap gap-3"><label className="grid gap-1 text-sm">Moneda<CustomSelect value={currency} onChange={event => { setCurrency(event.target.value); setPage(0); }} className={input}><option value="">Todas, con importes separados</option>{currencies.map(code => <option key={code} value={code}>{code}</option>)}</CustomSelect></label><label className="grid gap-1 text-sm">Origen<CustomSelect value={kind} onChange={event => { setKind(event.target.value); setPage(0); }} className={input}><option value="">Todos</option>{Object.entries(kinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label></div></div>
      <div className="space-y-3">{sources.map(source => {
        const rule = config.overrides.find(item => item.source_key === source.key);
        const isManual = !source.fingerprint;
        return <details key={source.key} className="forecast-source"><summary><span className={`forecast-source-icon ${source.direction === "in" ? "forecast-positive" : "forecast-outgoing"}`}>{source.direction === "in" ? <ArrowDownLeft size={18} /> : <ArrowUpRight size={18} />}</span><span className="forecast-source-title"><strong>{source.title}</strong><span>{kinds[source.kind]} · {dateLabel(source.due_date)}{source.needs_review ? " · Requiere revisión" : ""}</span></span><span className={`forecast-source-amount ${source.direction === "in" ? "forecast-positive" : "forecast-outgoing"}`}>{money(source.amount, source.currency)}</span><ChevronDown size={17} aria-hidden="true" /></summary><div className="forecast-source-editor space-y-4"><p>{kinds[source.kind]} · {source.direction === "in" ? "Entrada" : "Salida"} · Vencimiento original {source.original_due_date} · {source.in_horizon ? "Dentro del horizonte" : "Fuera del horizonte"}{source.is_overdue ? " · Vencido, proyectado para hoy" : ""}</p><p className="text-xs text-slate-500">{source.note}</p>{source.needs_review && <p className="text-xs text-red-700">La regla requiere revisión y quedó excluida del cálculo.</p>}
          {!isManual && <div className="grid gap-3 md:grid-cols-4"><label className="forecast-include"><input type="checkbox" role="switch" checked={rule?.included ?? source.default_included} disabled={!canWrite || busy} onChange={event => setRule(source, { included: event.target.checked })} />Incluir</label><label className="grid gap-1 text-xs">Fecha prevista<input type="date" className={input} value={rule?.due_date || source.due_date} disabled={!canWrite || busy} onChange={event => setRule(source, { due_date: event.target.value || null })} /></label><label className="grid gap-1 text-xs">Importe de la hipótesis<input type="number" className={input} min="0.000001" step="0.000001" max={source.source_amount || source.amount} value={rule?.amount || source.source_amount || source.amount} disabled={!canWrite || busy} onChange={event => setRule(source, { amount: event.target.value || null })} /></label><label className="grid gap-1 text-xs">Punto de custodia<CustomSelect className={input} value={rule?.point_key || source.point_key || ""} disabled={!canWrite || busy || source.fixed_point} onChange={event => setRule(source, { point_key: event.target.value || null })}><option value="">Sin asignar</option>{activePoints.filter(point => point.currency === source.currency).map(point => <option key={point.key} value={point.key}>{point.name}</option>)}</CustomSelect></label></div>}
          {!isManual && canWrite && <div className="flex gap-2"><button className={button} disabled={busy} onClick={() => setRule(source, {})}>Confirmar hipótesis con datos actuales</button>{rule && <button className={button} disabled={busy} onClick={() => setConfig(previous => ({ ...previous, overrides: previous.overrides.filter(item => item.source_key !== source.key) }))}>Restablecer documento</button>}</div>}
        </div></details>;
      })}{sources.length === 0 && <p className="forecast-empty">No hay documentos para estos filtros.</p>}</div><TablePagination page={page} pageSize={pageSize} total={filtered.length} loading={loading} onPageChange={setPage} onPageSizeChange={size => { setPageSize(size); setPage(0); }} />
      {config.overrides.filter(rule => !forecast.items.some(item => item.key === rule.source_key)).map(rule => <div key={rule.source_key} className="rounded-lg bg-amber-50 p-3 text-sm"><p>Documento que ya no está pendiente: {rule.source_key}</p><button className={button} disabled={!canWrite || busy} onClick={() => setConfig(previous => ({ ...previous, overrides: previous.overrides.filter(item => item.source_key !== rule.source_key) }))}>Quitar regla obsoleta</button></div>)}
      </section>}
    </>}
    {activeTab === "manual" && <section role="tabpanel" id={`${panelId}-panel-manual`} aria-labelledby={`${panelId}-tab-manual`}><details open={config.manual_events.length > 0}><summary className="cursor-pointer text-sm font-medium">Operaciones manuales del escenario</summary><div className="mt-3 space-y-3">{config.manual_events.map(item => <article className="space-y-2 rounded-lg border p-3" key={item.id}><div className="grid gap-2 md:grid-cols-3"><label className="grid gap-1 text-xs">Concepto<input className={input} required minLength={3} maxLength={255} disabled={busy || !canWrite} value={item.title} onChange={event => changeManual(item.id, { title: event.target.value })} /></label><label className="grid gap-1 text-xs">Tipo<CustomSelect className={input} disabled={busy || !canWrite} value={item.direction} onChange={event => changeManual(item.id, { direction: event.target.value as ManualEvent["direction"], point_key: null, destination_key: null })}><option value="in">Entrada prevista</option><option value="out">Salida prevista</option><option value="transfer">Traspaso interno simulado</option></CustomSelect></label><label className="grid gap-1 text-xs">Moneda<input className={input} disabled={busy || !canWrite} maxLength={3} pattern="[A-Z]{3}" value={item.currency} onChange={event => changeManual(item.id, { currency: event.target.value.toUpperCase(), point_key: null, destination_key: null })} /></label><label className="grid gap-1 text-xs">Importe<input type="number" className={input} disabled={busy || !canWrite} min="0.000001" step="0.000001" value={item.amount} onChange={event => changeManual(item.id, { amount: event.target.value })} /></label><label className="grid gap-1 text-xs">Fecha<input type="date" className={input} disabled={busy || !canWrite} min={forecast?.business_date} value={item.due_date} onChange={event => changeManual(item.id, { due_date: event.target.value })} /></label><label className="grid gap-1 text-xs">{item.direction === "transfer" ? "Origen del traspaso" : "Punto de custodia"}<CustomSelect className={input} disabled={busy || !canWrite} value={item.point_key || ""} onChange={event => changeManual(item.id, { point_key: event.target.value || null })}><option value="">Sin asignar</option>{activePoints.filter(point => point.currency === item.currency).map(point => <option key={point.key} value={point.key}>{point.name}</option>)}</CustomSelect></label>{item.direction === "transfer" && <label className="grid gap-1 text-xs">Destino del traspaso<CustomSelect className={input} disabled={busy || !canWrite} value={item.destination_key || ""} onChange={event => changeManual(item.id, { destination_key: event.target.value || null })}><option value="">Seleccione destino</option>{activePoints.filter(point => point.currency === item.currency && point.key !== item.point_key).map(point => <option key={point.key} value={point.key}>{point.name}</option>)}</CustomSelect></label>}</div><button className={button} disabled={busy || !canWrite} onClick={() => setConfig(previous => ({ ...previous, manual_events: previous.manual_events.filter(row => row.id !== item.id) }))}>Quitar hipótesis</button></article>)}{canWrite && <button className={button} disabled={busy || !forecast || config.manual_events.length >= 200} onClick={() => setConfig(previous => ({ ...previous, manual_events: [...previous.manual_events, { id: crypto.randomUUID(), title: "Nueva hipótesis", direction: "out", currency: currencies[0] || "PEN", amount: "1", due_date: forecast?.business_date || "", point_key: null, destination_key: null }] }))}>Añadir operación prevista</button>}<p className="text-xs text-slate-500">Un traspaso simulado descuenta el origen y aumenta el destino por el mismo importe y moneda. Las hipótesis no crean operaciones reales. Si proyecta solo una parte de un documento, el resto queda fuera de ese escenario.</p></div></details></section>}
    {detailDay && <ModalSurface labelledBy={`${panelId}-detail-title`} onClose={() => setDetailDay(null)} className="forecast-modal">
      <section className="forecast-modal-content"><header><div><h2 id={`${panelId}-detail-title`}>Compromisos del {dateLabel(detailDay.date)}</h2><p>{timeline?.name} · {detailDay.source_keys.length} documentos</p></div><button type="button" className={button} aria-label="Cerrar compromisos" onClick={() => setDetailDay(null)}><X size={18} /></button></header><div className="forecast-modal-body"><div className="forecast-modal-totals"><span>Entradas <strong className="forecast-positive">{money(detailDay.incoming, timeline?.currency || "")}</strong></span><span>Salidas <strong className="forecast-outgoing">{money(detailDay.outgoing, timeline?.currency || "")}</strong></span></div><div className="forecast-commitments">{detailSources.slice(detailPage * detailPageSize, (detailPage + 1) * detailPageSize).map(source => <article key={source.key}><div><strong>{source.title}</strong><p>{kinds[source.kind] || "Compromiso"} · {source.direction === "in" ? "Entrada" : "Salida"}</p></div><strong className={source.direction === "in" ? "forecast-positive" : "forecast-outgoing"}>{source.amount ? money(source.amount, source.currency) : "—"}</strong></article>)}</div></div><footer><TablePagination page={detailPage} pageSize={detailPageSize} total={detailSources.length} onPageChange={setDetailPage} onPageSizeChange={size => { setDetailPageSize(size); setDetailPage(0); }} /></footer></section>
    </ModalSurface>}
  </section>;
}

function amount(value: string) {
  return Number(value).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function money(value: string, currency: string) {
  return `${currency} ${amount(value)}`;
}
function dateLabel(value: string) {
  const [year, month, day] = value.split("-");
  return year && month && day ? `${day}/${month}/${year}` : value;
}
