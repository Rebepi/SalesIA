import { selectorSeed } from "../../../api/selectorSeed";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowRight, ClipboardList, Hash, Plus, RefreshCw, ShieldCheck, UserRound, X } from "lucide-react";
import "./warranty-workspace.css";
import { apiClient } from "../../../api/client";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

type Claim = { id: string; receipt: string; product_name: string; product_id: string; sale_id: string; serial_number: string | null; quantity: string; claim_date: string; warranty_until: string | null; policy_snapshot: string | null; status: string; version: number; assigned_name: string | null; issue_description: string; diagnosis: string | null; resolution: string | null; history: { action: string; status: string; actor: string; at: string; notes: string; coverage_source?: string }[] };
type Eligible = { sale_id: string; sale_line_id: string; receipt: string; customer_name: string; quantity: string; warranty_until: string; serial_numbers: string[]; coverage_source: string };
type Product = { id: string; name: string; sku: string };
const statuses: Record<string, string> = { open: "Abierta", diagnosis: "En diagnóstico", awaiting_parts: "Esperando repuestos", repairing: "En reparación", ready: "Lista para entregar", delivered: "Entregada", rejected: "Rechazada", cancelled: "Cancelada" };
const actions: Record<string, string> = { assign: "Asignar responsable", diagnose: "Registrar diagnóstico", await_parts: "Esperar repuestos", repair: "Iniciar reparación", ready: "Marcar lista para entregar", deliver: "Registrar entrega final", reject: "Rechazar garantía", cancel: "Cancelar expediente" };
const input = "warranty-input mt-1 w-full";
const button = "warranty-button";

export function WarrantyWorkspace({ canWrite }: { canWrite: boolean }) {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [members, setMembers] = useState<{ id: string; name: string }[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Claim | null>(null);
  const [creating, setCreating] = useState(false);
  const [product, setProduct] = useState<Product | undefined>();
  const [eligible, setEligible] = useState<Eligible[]>([]);
  const [lineId, setLineId] = useState("");
  const [action, setAction] = useState("assign");
  const dialog = useRef<HTMLDialogElement>(null);
  const writeLock = useRef(false);
  const pending = useRef(new Map<string, string>());
  const activeLine = eligible.find(line => line.sale_line_id === lineId);

  function failureMessage(failure: unknown) { const detail = (failure as { detail?: unknown }).detail; return typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo completar la operación."; }
  async function load() {
    setLoading(true);
    setError("");
    try {
      const [result, options] = await Promise.all([apiClient.request<{ items: Claim[]; total_count: number }>(`/api/v1/warranty-cases?limit=25&offset=${page * 25}${status ? `&status=${status}` : ""}`), selectorSeed<{ id: string; name: string }>("people", { active_only: "true" })]);
      setClaims(result.items);
      setTotal(result.total_count);
      setMembers(options);
      return result.items;
    } catch (failure) { setError(failureMessage(failure)); return []; }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [page, status]);
  useEffect(() => { if (selected || creating) dialog.current?.showModal(); else dialog.current?.close(); }, [Boolean(selected), creating]);
  useEffect(() => {
    setEligible([]);
    setLineId("");
    if (!product) return;
    const controller = new AbortController();
    apiClient.request<{ items: Eligible[] }>(`/api/v1/products/${product.id}/eligible-warranty-sales`, { signal: controller.signal }).then(result => setEligible(result.items)).catch(failure => { if (!controller.signal.aborted) setError(failureMessage(failure)); });
    return () => controller.abort();
  }, [product?.id]);
  async function write(path: string, body: unknown) {
    if (writeLock.current) return false;
    writeLock.current = true;
    setBusy(true);
    setError("");
    const signature = JSON.stringify({ path, body });
    const key = pending.current.get(signature) || crypto.randomUUID();
    pending.current.set(signature, key);
    try {
      const result = await apiClient.request<Claim>(path, { method: "POST", body: JSON.stringify(body), headers: { "Idempotency-Key": key } });
      pending.current.delete(signature);
      setCreating(false);
      setSelected(result);
      await load();
      return true;
    } catch (failure) { setError(failureMessage(failure)); return false; }
    finally { writeLock.current = false; setBusy(false); }
  }
  function close() { if (!busy) { setSelected(null); setCreating(false); } }
  function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!product || !activeLine) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void write("/api/v1/products/warranty/claims", { ...values, product_id: product.id, sale_id: activeLine.sale_id, sale_line_id: activeLine.sale_line_id, serial_number: values.serial_number || null });
  }
  function submitAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void write(`/api/v1/warranty-cases/${selected.id}/actions`, { ...values, action, version: selected.version, assigned_to: values.assigned_to || null });
  }
  function permittedActions(claim: Claim) {
    const result = ["assign"];
    if (claim.status === "open") result.push("diagnose", "reject", "cancel");
    if (claim.status === "diagnosis") result.push("await_parts", "repair", "ready", "reject", "cancel");
    if (claim.status === "awaiting_parts") result.push("repair", "cancel");
    if (claim.status === "repairing") result.push("await_parts", "ready");
    if (claim.status === "ready") result.push("deliver");
    return result;
  }
  return <div className="warranty-workspace space-y-5"><div className="warranty-toolbar"><label className="warranty-status-filter text-sm">Estado<CustomSelect searchable={false} className={input} value={status} onChange={event => { setStatus(event.target.value); setPage(0); }}><option value="">Todos los estados</option>{Object.entries(statuses).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</CustomSelect></label><div className="warranty-toolbar-count"><span className="warranty-icon"><ShieldCheck size={20} aria-hidden="true" /></span><div><strong>{total} {total === 1 ? "expediente" : "expedientes"}</strong><p>{status ? statuses[status] : "Todos los estados"}</p></div></div><div className="warranty-toolbar-actions"><button className={button} onClick={() => void load()} disabled={loading || busy}><RefreshCw size={16} className={loading ? "animate-spin" : ""} aria-hidden="true" />Actualizar</button>{canWrite && <button className={`${button} warranty-primary`} onClick={() => { setCreating(true); setSelected(null); setProduct(undefined); setError(""); }}><Plus size={17} aria-hidden="true" />Nuevo expediente</button>}</div></div>{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{loading && <p role="status" className="text-sm">Cargando…</p>}<div className="grid gap-4 lg:grid-cols-2" aria-busy={loading}>{claims.map(claim => <button key={claim.id} className="warranty-card" onClick={() => { setSelected(claim); setCreating(false); setAction("assign"); }}>
      <span className="warranty-card-top"><span className="warranty-receipt"><ClipboardList size={16} aria-hidden="true" />{claim.receipt}</span><span className={`warranty-status warranty-status-${claim.status}`}>{statuses[claim.status] || claim.status}</span></span>
      <strong className="warranty-product">{claim.product_name}</strong><p className="warranty-issue">{claim.issue_description}</p>
      <span className="warranty-card-bottom"><span className="warranty-card-meta"><span><Hash size={14} aria-hidden="true" />{claim.serial_number ? `Serie ${claim.serial_number}` : `${claim.quantity} unidades`}</span><span><UserRound size={14} aria-hidden="true" />{claim.assigned_name || "Sin responsable asignado"}</span></span><ArrowRight size={18} className="warranty-card-arrow" aria-hidden="true" /></span>
    </button>)}</div>{!loading && !claims.length && <div className="warranty-empty"><span className="warranty-icon"><ShieldCheck size={30} aria-hidden="true" /></span><h2>No hay expedientes para esta selección</h2><p>{status ? "Selecciona otro estado para consultar las garantías." : "Los expedientes de garantía aparecerán aquí cuando se registren."}</p></div>}<div className="warranty-pagination"><span className="text-sm">{total} {total === 1 ? "expediente" : "expedientes"} · página {page + 1}</span><div className="flex gap-2"><button className={button} disabled={page === 0 || loading} onClick={() => setPage(value => value - 1)}>Anterior</button><button className={button} disabled={(page + 1) * 25 >= total || loading} onClick={() => setPage(value => value + 1)}>Siguiente</button></div></div>
    <dialog ref={dialog} onCancel={event => { event.preventDefault(); close(); }} aria-labelledby="warranty-dialog-title" className="warranty-dialog shadow-xl backdrop:bg-slate-950/60"><div className="warranty-dialog-heading"><span className="warranty-icon"><ShieldCheck size={23} aria-hidden="true" /></span><div className="min-w-0 flex-1"><h2 id="warranty-dialog-title" className="text-lg font-semibold">{creating ? "Nuevo expediente de garantía" : selected?.product_name}</h2>{creating && <p className="warranty-dialog-subtitle">Selecciona la venta y registra el problema del producto.</p>}</div><button type="button" className={`${button} warranty-close`} aria-label="Cerrar expediente" disabled={busy} onClick={close}><X size={20} aria-hidden="true" /></button></div>{error && <p role="alert" className="warranty-dialog-error text-sm text-red-700">{error}</p>}{creating && <form onSubmit={submitCreate} className="warranty-create-form">
      <div className="warranty-form-body">
        <section className="warranty-form-section" aria-labelledby="warranty-sale-heading">
          <h3 id="warranty-sale-heading" className="warranty-form-section-title"><ClipboardList size={17} aria-hidden="true" />Producto y venta</h3>
          <RemoteEntitySelect<Product> value={product?.id || ""} onChange={(_, option) => setProduct(option?.data)} endpoint="/api/v1/products" entityType="product" label="Producto" placeholder="Buscar por nombre o SKU" mapOption={item => ({ value: item.id, label: `${item.sku} · ${item.name}`, data: item })} initialOption={product ? { value: product.id, label: product.name, data: product } : undefined} required />
          <label className="block text-sm">Venta y línea elegible<span className="warranty-required" aria-hidden="true"> *</span><CustomSelect searchable={true} className={input} value={lineId} onChange={event => setLineId(event.target.value)} required><option value="">Seleccionar venta</option>{eligible.map(line => <option key={line.sale_line_id} value={line.sale_line_id}>{line.receipt} · {line.customer_name} · {line.quantity} unidades</option>)}</CustomSelect></label>
          {product && !eligible.length && <p className="warranty-form-hint">No se encontraron ventas con cobertura vigente.</p>}
          {activeLine && <p className="warranty-coverage"><ShieldCheck size={16} aria-hidden="true" /><span>Cobertura hasta {new Date(activeLine.warranty_until).toLocaleDateString("es-PE", { timeZone: "America/Lima" })}{activeLine.coverage_source === "legacy_current_policy" ? " · Venta histórica: cobertura estimada con la política actual." : " · Condiciones conservadas en la venta."}</span></p>}
        </section>
        <section className="warranty-form-section" aria-labelledby="warranty-issue-heading">
          <h3 id="warranty-issue-heading" className="warranty-form-section-title"><ClipboardList size={17} aria-hidden="true" />Detalle de la solicitud</h3>
          <div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm">Cantidad<span className="warranty-required" aria-hidden="true"> *</span><input className={input} name="quantity" type="number" min="0.000001" step="0.000001" defaultValue="1" required /></label>
          {activeLine && activeLine.serial_numbers.length > 0 && <label className="block text-sm">Serie<span className="warranty-required" aria-hidden="true"> *</span><CustomSelect searchable={true} className={input} name="serial_number" required><option value="">Seleccionar serie vendida</option>{activeLine.serial_numbers.map(serial => <option key={serial} value={serial}>{serial}</option>)}</CustomSelect></label>}</div>
          <label className="block text-sm">Descripción del problema<span className="warranty-required" aria-hidden="true"> *</span><textarea className={input} name="issue_description" placeholder="Describe la falla y cómo se presenta." required minLength={5} maxLength={4000} /></label>
        </section>
      </div>
      <div className="warranty-dialog-footer"><span className="warranty-form-hint">* Campos obligatorios</span><div className="flex flex-wrap gap-2"><button type="button" className={button} disabled={busy} onClick={close}>Cancelar</button><button type="submit" className={`${button} warranty-primary`} disabled={busy || !activeLine}>{busy ? <RefreshCw size={16} className="animate-spin" aria-hidden="true" /> : <Plus size={16} aria-hidden="true" />}{busy ? "Guardando…" : "Abrir expediente"}</button></div></div>
    </form>}{selected && <div className="warranty-selected-body space-y-4"><p className="text-sm">{selected.receipt} · {statuses[selected.status]} · versión {selected.version}</p><p className="text-sm">{selected.issue_description}</p><p className="text-xs text-slate-500">{selected.assigned_name || "Sin asignar"}{selected.warranty_until ? ` · Cobertura hasta ${new Date(selected.warranty_until).toLocaleDateString("es-PE", { timeZone: "America/Lima" })}` : " · Expediente histórico sin vencimiento conservado"}</p>{selected.policy_snapshot && <p className="warranty-policy text-sm">{selected.policy_snapshot}</p>}{selected.diagnosis && <p className="text-sm"><strong>Diagnóstico:</strong> {selected.diagnosis}</p>}{selected.resolution && <p className="text-sm"><strong>Resolución:</strong> {selected.resolution}</p>}<h3 className="font-medium">Historial</h3>{selected.history.map((event, index) => <div key={index} className="warranty-history-event text-sm"><strong>{statuses[event.status] || event.status}</strong><p>{event.notes}</p><p className="mt-1 text-xs text-slate-500">{event.actor} · {new Date(event.at).toLocaleString("es-PE", { timeZone: "America/Lima" })}</p></div>)}{canWrite && !["delivered", "cancelled", "rejected"].includes(selected.status) && <form onSubmit={submitAction} className="warranty-action-form space-y-4"><label className="block text-sm">Acción<CustomSelect searchable={false} className={input} value={action} onChange={event => setAction(event.target.value)}>{permittedActions(selected).map(key => <option key={key} value={key}>{actions[key]}</option>)}</CustomSelect></label>{action === "assign" && <label className="block text-sm">Responsable<CustomSelect remote={{ resource: "people", active_only: true }} searchable={true} className={input} name="assigned_to" required><option value="">Seleccionar</option>{members.map(member => <option key={member.id} value={member.id}>{member.name}</option>)}</CustomSelect></label>}<label className="block text-sm">Notas o resultado<textarea className={input} name="notes" required minLength={3} maxLength={4000} /></label><button className={`${button} warranty-primary`} disabled={busy}>Registrar acción</button></form>}</div>}</dialog>
  </div>;
}
