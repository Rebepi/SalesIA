import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { FileSearch, FolderOpen, Layers3, Search, SlidersHorizontal } from "lucide-react";
import "./business-records.css";
import { apiClient } from "../../../api/client";
import { useUnsavedChanges } from "../../../ui/drafts";
import { RecordNavigation } from "./RecordNavigation";

type Resource = { type: string; label: string; can_write: boolean };
type RecordItem = { type: string; id: string; title: string; status: string; version: number | null; currency: string | null; amount: string | null; created_at: string | null };
type Dossier = { resource: RecordItem; related: RecordItem[]; events: { id: string; action: string; actor: string; entity_id: string; date: string; changes: unknown }[]; audit_available: boolean };
type Definition = { id: string; key: string; label: string; field_type: "text" | "decimal" | "date" | "boolean" | "choice"; options: string[]; required_states: string[]; is_active: boolean; version: number };
type FieldValues = { version: number; values: Record<string, string | boolean | null>; definitions: Definition[]; state: string };
const input = "records-input mt-1 w-full";
const button = "records-button";
const stateLabels: Record<string, string> = { draft: "Borrador", pending: "Pendiente", pending_approval: "Por aprobar", confirmed: "Confirmado", active: "Activo", inactive: "Inactivo", submitted: "Presentado", approved: "Aprobado", paid: "Pagado", partial: "Parcial", cancelled: "Cancelado", superseded: "Reemplazado", accepted: "Aceptado", rejected: "Rechazado", delivered: "Entregado", completed: "Completado", fulfilled: "Atendido", partially_fulfilled: "Atendido parcialmente", open: "Abierto" };

function errorMessage(failure: unknown) {
  const detail = (failure as { detail?: unknown }).detail;
  return typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo completar la operación.";
}

export function BusinessRecordsWorkspace({ canConfigure, storageScope }: { canConfigure: boolean; storageScope: string }) {
  const [catalog, setCatalog] = useState<Resource[]>([]);
  const [kind, setKind] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [items, setItems] = useState<RecordItem[]>([]);
  const [total, setTotal] = useState(0);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [fields, setFields] = useState<FieldValues | null>(null);
  const [values, setValues] = useState<Record<string, string | boolean | null>>({});
  const [definitions, setDefinitions] = useState<Definition[]>([]);
  const [editingDefinition, setEditingDefinition] = useState<Definition | null>(null);
  const [definitionOpen, setDefinitionOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fieldFilter, setFieldFilter] = useState("");
  const [fieldFilterValue, setFieldFilterValue] = useState("");
  const loadVersion = useRef(0);
  const recordLoadVersion = useRef(0);
  const writeLock = useRef(false);
  const pendingKeys = useRef(new Map<string, string>());
  const definitionDialog = useRef<HTMLDialogElement>(null);
  const dirty = Boolean(fields && JSON.stringify(values) !== JSON.stringify(fields.values));
  useUnsavedChanges(dirty);
  const activeResource = catalog.find(resource => resource.type === kind);

  useEffect(() => {
    let active = true;
    recordLoadVersion.current += 1;
    setDossier(null);
    setFields(null);
    setValues({});
    apiClient.request<Resource[]>("/api/v1/business/resources").then(result => {
      if (!active) return;
      setCatalog(result);
      let saved: { kind?: string; query?: string; page?: number; fieldFilter?: string; fieldFilterValue?: string } = {};
      try { saved = JSON.parse(sessionStorage.getItem(`salesia_records:${storageScope}`) || "{}"); } catch { saved = {}; }
      setKind(result.some(resource => resource.type === saved.kind) ? saved.kind || "" : result[0]?.type || "");
      setQuery(saved.query || "");
      setPage(Math.max(0, saved.page || 0));
      setFieldFilter(saved.fieldFilter || "");
      setFieldFilterValue(saved.fieldFilterValue || "");
    }).catch(failure => { if (active) setError(errorMessage(failure)); });
    return () => { active = false; };
  }, [storageScope]);

  useEffect(() => {
    if (!kind) return;
    sessionStorage.setItem(`salesia_records:${storageScope}`, JSON.stringify({ kind, query, page, fieldFilter, fieldFilterValue }));
    const version = ++loadVersion.current;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const parameters = new URLSearchParams({ q: query, limit: "25", offset: String(page * 25) });
        if (fieldFilter) { parameters.set("field_key", fieldFilter); parameters.set("field_value", fieldFilterValue); }
        const [result, defs] = await Promise.all([apiClient.request<{ items: RecordItem[]; total_count: number }>(`/api/v1/business/records/${kind}?${parameters}`, { signal: controller.signal }), apiClient.request<Definition[]>(`/api/v1/business/field-definitions/${kind}`, { signal: controller.signal })]);
        if (version !== loadVersion.current) return;
        setItems(result.items);
        setTotal(result.total_count);
        setDefinitions(defs);
      } catch (failure) { if (!controller.signal.aborted && version === loadVersion.current) setError(errorMessage(failure)); }
      finally { if (version === loadVersion.current) setLoading(false); }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [kind, query, page, storageScope, fieldFilter, fieldFilterValue]);

  useEffect(() => {
    if (definitionOpen) definitionDialog.current?.showModal();
    else definitionDialog.current?.close();
  }, [definitionOpen]);

  useEffect(() => {
    if (!catalog.length) return;
    const openContext = () => {
      const raw = sessionStorage.getItem("salesia_record_context");
      if (!raw) return;
      try {
        const context = JSON.parse(raw) as { type: string; id: string };
        if (!catalog.some(resource => resource.type === context.type)) return;
        sessionStorage.removeItem("salesia_record_context");
        setKind(context.type);
        void openRecord(context.type, context.id);
      } catch { setError("El registro solicitado no está disponible."); }
    };
    openContext();
    window.addEventListener("salesia:open-record", openContext);
    return () => window.removeEventListener("salesia:open-record", openContext);
  }, [catalog]);

  async function openRecord(type: string, id: string) {
    if (dirty && !window.confirm("Hay campos sin guardar. ¿Descartar los cambios y abrir otro registro?")) return;
    const requestVersion = ++recordLoadVersion.current;
    setLoading(true);
    setError("");
    try {
      const [result, fieldValues] = await Promise.all([apiClient.request<Dossier>(`/api/v1/business/records/${type}/${id}`), apiClient.request<FieldValues>(`/api/v1/business/fields/${type}/${id}`)]);
      if (requestVersion !== recordLoadVersion.current) return;
      setDossier(result);
      setFields(fieldValues);
      setValues(fieldValues.values);
    } catch (failure) { if (requestVersion === recordLoadVersion.current) setError(errorMessage(failure)); }
    finally { if (requestVersion === recordLoadVersion.current) setLoading(false); }
  }

  async function save(path: string, body: unknown) {
    if (writeLock.current) return false;
    writeLock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const signature = JSON.stringify({ path, body });
    const key = pendingKeys.current.get(signature) || crypto.randomUUID();
    pendingKeys.current.set(signature, key);
    try {
      await apiClient.request(path, { method: "PUT", body: JSON.stringify(body), headers: { "Idempotency-Key": key } });
      pendingKeys.current.delete(signature);
      setNotice("Cambios guardados.");
      return true;
    } catch (failure) { setError(errorMessage(failure)); return false; }
    finally { setBusy(false); writeLock.current = false; }
  }

  async function saveFields(event: FormEvent) {
    event.preventDefault();
    if (!dossier || !fields) return;
    const valuesToSave = Object.fromEntries(Object.entries(values).filter(([key]) => fields.definitions.some(field => field.is_active && field.key === key)));
    if (await save(`/api/v1/business/fields/${dossier.resource.type}/${dossier.resource.id}`, { version: fields.version, values: valuesToSave })) {
      const result = await apiClient.request<FieldValues>(`/api/v1/business/fields/${dossier.resource.type}/${dossier.resource.id}`);
      setFields(result);
      setValues(result.values);
      setDossier(await apiClient.request<Dossier>(`/api/v1/business/records/${dossier.resource.type}/${dossier.resource.id}`));
    }
  }

  async function saveDefinition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const body = { key: String(data.get("key")), label: String(data.get("label")), field_type: String(data.get("field_type")), options: String(data.get("options") || "").split("\n").map(value => value.trim()).filter(Boolean), required_states: String(data.get("required_states") || "").split(",").map(value => value.trim()).filter(Boolean), is_active: data.get("is_active") === "on", version: editingDefinition?.version || 0 };
    if (await save(`/api/v1/business/field-definitions/${kind}`, body)) {
      setDefinitions(await apiClient.request<Definition[]>(`/api/v1/business/field-definitions/${kind}`));
      setDefinitionOpen(false);
      if (dossier?.resource.type === kind) await openRecord(kind, dossier.resource.id);
    }
  }

  function recordCard(item: RecordItem, compact = false) {
    const selected = dossier?.resource.type === item.type && dossier.resource.id === item.id;
    return <button key={`${item.type}:${item.id}`} type="button" aria-pressed={selected} className={`records-record ${selected ? "is-selected" : ""}`} onClick={() => void openRecord(item.type, item.id)}>
      <span className="records-record-meta"><span>{catalog.find(resource => resource.type === item.type)?.label}</span><span className="records-status">{stateLabels[item.status] || item.status}</span></span>
      <strong className="mt-2 block text-sm">{item.title}</strong>
      {item.amount !== null && <span className="mt-2 block text-sm font-semibold">{item.currency} {item.amount}</span>}
      {!compact && item.created_at && <span className="records-muted mt-2 block text-xs">{new Date(item.created_at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</span>}
    </button>;
  }

  return <div className="business-records space-y-5">{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="rounded-xl bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
    <RecordNavigation storageScope={storageScope} active={dossier?.resource || null} selection={{ kind, query, fieldFilter, fieldFilterValue }} onOpen={(type, id) => { void openRecord(type, id); }} canShare={canConfigure} onFilter={filter => { if (dirty && !window.confirm("¿Descartar los campos sin guardar?")) return; setKind(filter.kind); setQuery(filter.query); setFieldFilter(filter.fieldFilter); setFieldFilterValue(filter.fieldFilterValue); setPage(0); setDossier(null); setFields(null); }} />
    <div className="records-panel records-filters"><div className="records-section-title"><SlidersHorizontal size={18} aria-hidden="true" /><h2>Buscar expedientes</h2></div><div className="grid gap-4 md:grid-cols-3"><label className="text-sm">Tipo de registro<CustomSelect searchable={true} className={input} value={kind} onChange={event => { if (dirty && !window.confirm("¿Descartar los campos sin guardar?")) return; setKind(event.target.value); setPage(0); setDossier(null); setFields(null); setFieldFilter(""); }}><option value="">Seleccionar</option>{catalog.map(resource => <option key={resource.type} value={resource.type}>{resource.label}</option>)}</CustomSelect></label><label className="text-sm md:col-span-2">Buscar<input className={input} value={query} onChange={event => { setQuery(event.target.value); setPage(0); }} placeholder="Nombre, código o documento" /></label></div>
    {definitions.some(field => field.is_active) && <div className="records-extra-filters grid gap-4 sm:grid-cols-2"><label className="text-sm">Filtrar por campo<CustomSelect searchable={true} className={input} value={fieldFilter} onChange={event => { setFieldFilter(event.target.value); setPage(0); }}><option value="">Sin filtro adicional</option>{definitions.filter(field => field.is_active).map(field => <option key={field.key} value={field.key}>{field.label}</option>)}</CustomSelect></label><label className="text-sm">Valor exacto<input className={input} disabled={!fieldFilter} value={fieldFilterValue} onChange={event => { setFieldFilterValue(event.target.value); setPage(0); }} /></label></div>}</div>
    <div className="records-columns grid items-start gap-5 xl:grid-cols-[minmax(240px,0.75fr)_minmax(0,1.5fr)]"><section className="records-panel records-list space-y-3" aria-label="Registros encontrados"><div className="records-list-heading"><div><h2 className="font-semibold">Registros</h2><p className="records-muted mt-1 text-xs">{total} {total === 1 ? "resultado" : "resultados"}</p></div>{canConfigure && kind && <button className={`${button} records-button-primary`} onClick={() => { setEditingDefinition(null); setDefinitionOpen(true); }}>Nuevo campo</button>}</div>{loading && <p role="status" className="text-sm text-slate-500">Cargando…</p>}<div className="records-results" aria-busy={loading}>{items.map(item => recordCard(item))}</div>{!loading && !items.length && <div className="records-empty records-empty-list"><Search size={28} aria-hidden="true" /><h3>Sin resultados</h3><p>Prueba con otro tipo de registro o ajusta tu búsqueda.</p></div>}<div className="records-pagination"><button className={button} disabled={page === 0 || loading} onClick={() => setPage(value => value - 1)}>Anterior</button><span className="records-muted text-xs">Página {page + 1}</span><button className={button} disabled={(page + 1) * 25 >= total || loading} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>{canConfigure && definitions.length > 0 && <details className="records-manage"><summary className="cursor-pointer text-sm font-medium">Administrar campos</summary><div className="mt-3 space-y-2">{definitions.map(field => <button key={field.id} className={`${button} block w-full text-left`} onClick={() => { setEditingDefinition(field); setDefinitionOpen(true); }}>{field.label} · {field.is_active ? "Activo" : "Inactivo"}</button>)}</div></details>}</section>
    <section className="min-w-0 space-y-5" aria-label="Detalle del expediente">{!dossier ? <div className="records-panel records-empty records-empty-detail"><span className="records-icon"><FolderOpen size={32} aria-hidden="true" /></span><h2>Tu expediente, en un solo lugar</h2><p>Selecciona un registro para ver sus datos, documentos relacionados e historial de cambios.</p><span className="records-empty-hint"><FileSearch size={16} aria-hidden="true" />Busca y selecciona en la lista de registros</span></div> : <><div className="records-panel records-detail"><h2 className="text-lg font-semibold">{dossier.resource.title}</h2><p className="mt-1 text-sm text-slate-500">{stateLabels[dossier.resource.status] || dossier.resource.status}{dossier.resource.version ? ` · versión ${dossier.resource.version}` : ""}</p><h3 className="records-subheading">Datos adicionales</h3>{fields && <form onSubmit={saveFields} className="records-fields mt-4 grid gap-4 sm:grid-cols-2">{fields.definitions.filter(field => field.is_active).map(field => <label className="block text-sm" key={field.key}>{field.label}{field.required_states.length > 0 && <span className="ml-2 text-xs text-slate-500">Obligatorio: {field.required_states.map(state => state === "*" ? "siempre" : stateLabels[state] || state).join(", ")}</span>}{field.field_type === "boolean" ? <CustomSelect searchable={false} className={input} disabled={!catalog.find(resource => resource.type === dossier.resource.type)?.can_write || busy} value={values[field.key] === null || values[field.key] === undefined ? "" : String(values[field.key])} onChange={event => setValues(current => ({ ...current, [field.key]: event.target.value === "" ? null : event.target.value === "true" }))}><option value="">Sin indicar</option><option value="true">Sí</option><option value="false">No</option></CustomSelect> : field.field_type === "choice" ? <CustomSelect searchable={true} className={input} disabled={!catalog.find(resource => resource.type === dossier.resource.type)?.can_write || busy} value={String(values[field.key] || "")} onChange={event => setValues(current => ({ ...current, [field.key]: event.target.value }))}><option value="">Sin indicar</option>{field.options.map(option => <option key={option} value={option}>{option}</option>)}</CustomSelect> : <input className={input} disabled={!catalog.find(resource => resource.type === dossier.resource.type)?.can_write || busy} type={field.field_type === "date" ? "date" : field.field_type === "decimal" ? "number" : "text"} step={field.field_type === "decimal" ? "0.000001" : undefined} maxLength={4000} value={String(values[field.key] ?? "")} onChange={event => setValues(current => ({ ...current, [field.key]: event.target.value }))} />}</label>)}{!fields.definitions.some(field => field.is_active) && <p className="text-sm text-slate-500">Este tipo de registro no tiene campos adicionales activos.</p>}{fields.definitions.some(field => field.is_active) && catalog.find(resource => resource.type === dossier.resource.type)?.can_write && <button className={`${button} records-button-primary records-save`} disabled={!dirty || busy}>Guardar datos adicionales</button>}</form>}</div><div className="records-panel records-detail"><div className="records-section-title"><Layers3 size={18} aria-hidden="true" /><h3>Documentos y registros relacionados</h3></div><p className="mt-1 text-xs text-slate-500">Se muestran hasta 100 registros por relación, respetando tus permisos.</p><div className="mt-3 grid gap-2 md:grid-cols-2">{dossier.related.map(item => recordCard(item, true))}</div>{!dossier.related.length && <p className="mt-3 text-sm text-slate-500">No hay relaciones disponibles para tu usuario.</p>}</div><div className="records-panel records-detail"><h3 className="font-medium">Historial de cambios</h3>{!dossier.audit_available ? <p className="mt-3 text-sm text-slate-500">La consulta del historial requiere permiso de auditoría.</p> : <div className="mt-3 space-y-3">{dossier.events.map(event => <details key={event.id} className="records-event"><summary className="cursor-pointer text-sm"><strong>{event.action.split("_").join(" ")}</strong> · {event.actor}<span className="mt-1 block text-xs text-slate-500">{new Date(event.date).toLocaleString("es-PE", { timeZone: "America/Lima" })}</span></summary><div className="mt-3 whitespace-pre-wrap break-words text-xs text-slate-600">{JSON.stringify(event.changes, null, 2)}</div></details>)}{!dossier.events.length && <p className="text-sm text-slate-500">Sin eventos de auditoría disponibles.</p>}</div>}</div></>}</section></div>
    <dialog ref={definitionDialog} onCancel={event => { event.preventDefault(); if (!busy) setDefinitionOpen(false); }} aria-labelledby="records-definition-title" className="records-dialog max-h-[90vh] w-[min(95vw,640px)] rounded-2xl p-6 shadow-xl backdrop:bg-slate-950/60"><div className="mb-4 flex items-center justify-between"><h2 id="records-definition-title" className="text-lg font-semibold">{editingDefinition ? "Editar campo" : "Nuevo campo"} · {activeResource?.label}</h2><button className={button} disabled={busy} onClick={() => setDefinitionOpen(false)}>Cerrar</button></div>{error && <p role="alert" className="mb-3 text-sm text-red-700">{error}</p>}{definitionOpen && <form key={editingDefinition?.id || "new"} onSubmit={saveDefinition} className="space-y-4"><label className="block text-sm">Nombre interno del campo<input className={input} name="key" required pattern="[a-z][a-z0-9_]{0,63}" readOnly={Boolean(editingDefinition)} defaultValue={editingDefinition?.key} placeholder="Ejemplo: fecha_instalacion" /></label><label className="block text-sm">Etiqueta visible<input className={input} name="label" required minLength={2} maxLength={128} defaultValue={editingDefinition?.label} /></label><label className="block text-sm">Tipo<CustomSelect searchable={false} className={input} name="field_type" defaultValue={editingDefinition?.field_type || "text"}>{[["text", "Texto"], ["decimal", "Número"], ["date", "Fecha"], ["boolean", "Sí o no"], ["choice", "Lista de opciones"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label><label className="block text-sm">Opciones, una por línea<textarea className={input} name="options" defaultValue={editingDefinition?.options.join("\n")} /></label><label className="block text-sm">Estados en los que es obligatorio, separados por comas<input className={input} name="required_states" defaultValue={editingDefinition?.required_states.join(", ")} placeholder="confirmed, approved" /><span className="mt-1 block text-xs text-slate-500">Usa * si debe estar completo antes de cualquier transición protegida.</span></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_active" defaultChecked={editingDefinition?.is_active ?? true} />Campo activo</label><button className={`${button} records-button-primary`} disabled={busy}>Guardar definición</button></form>}</dialog>
  </div>;
}
