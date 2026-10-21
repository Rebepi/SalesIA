import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";

type Page<T> = { items: T[]; total_count: number; business_date?: string };
type Line = { product_id: string; name: string; sku: string; quantity: string; pending_quantity: string; shortage_claimable_quantity?: string; replacement_received?: string; replacement_committed?: string; replacement_available?: string };
type Source = { source_id: string; label: string; supplier_name: string; currency: string; lines: Line[] };
type Claim = { id: string; code: string; supplier_name: string; source_kind: string; source_id: string; purchase_order_id: string; currency: string; expected_amount: string; agreed_amount: string | null; resolution: string; reason_type: string; description: string; status: string; version: number; business_date: string; credits: { issued: string; available: string; applied: string }; items: Line[]; credit_documents: { id: string; reference: string; date: string; amount: string }[]; replacement_orders: { id: string; status: string }[]; history: { action: string; actor: string; at: string; notes: string }[] };
const states: Record<string, string> = { open: "Abierto", acknowledged: "Acuerdo registrado", credit_available: "Crédito disponible", partially_compensated: "Compensación parcial", resolved: "Compensado", rejected: "Rechazado", cancelled: "Cancelado" };
const resolutions: Record<string, string> = { credit: "Crédito del proveedor", discount: "Descuento compensatorio", replacement: "Reposición sin nueva deuda" };
const kinds: Record<string, string> = { purchase_order: "Orden de compra", goods_receipt: "Recepción", purchase_return: "Devolución", invoice_match: "Factura conciliada" };
const reasons: Record<string, string> = { return: "Devolución", shortage: "Faltante", overprice: "Sobreprecio", quality: "Calidad" };
const actions: Record<string, string> = { CREATE: "Creación", ACKNOWLEDGE: "Acuerdo", CREDIT_DOCUMENT: "Documento de crédito", REPLACEMENT_ORDER: "Orden de reposición", COMPENSATION_UPDATED: "Compensación actualizada", CANCEL: "Cancelación", REJECT: "Rechazo", REOPEN: "Reapertura" };
const field = "rounded-lg border border-slate-300 bg-white p-2 text-sm";
const button = "rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50";

function problem(cause: unknown) { const detail = (cause as { detail?: unknown }).detail; return typeof detail === "string" ? detail : cause instanceof Error ? cause.message : "No se pudo completar la operación."; }

export function SupplierClaimsPanel({ onChanged }: { onChanged?: () => void }) {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [rows, setRows] = useState<Page<Claim>>({ items: [], total_count: 0 });
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(0);
  const [detail, setDetail] = useState<Claim | null>(null);
  const [creating, setCreating] = useState(false);
  const [kind, setKind] = useState("purchase_return");
  const [sourcePage, setSourcePage] = useState(0);
  const [sources, setSources] = useState<Page<Source>>({ items: [], total_count: 0 });
  const [sourceId, setSourceId] = useState("");
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const detailRevision = useRef(0);
  const write = permissions.includes("purchases:write");
  const canReplace = write && permissions.some(value => ["purchases:approve", "approvals:manage", "organization:manage"].includes(value));
  const source = sources.items.find(item => item.source_id === sourceId);

  useEffect(() => { let active = true; void apiClient.getMe().then(profile => { if (active) setPermissions(profile.permissions || []); }).catch(cause => { if (active) setError(problem(cause)); }); return () => { active = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController();
    void apiClient.request<Page<Claim>>(`/api/v1/supplier-claims?limit=10&offset=${page * 10}${status ? `&status=${status}` : ""}`, { signal: controller.signal }).then(setRows).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [page, status, revision]);
  useEffect(() => {
    if (!creating || !permissions.includes("purchases:read")) return;
    const controller = new AbortController();
    setSources({ items: [], total_count: 0 });
    setSourceId("");
    setQuantities({});
    void apiClient.request<Page<Source>>(`/api/v1/supplier-claim-sources?kind=${kind}&limit=20&offset=${sourcePage * 20}`, { signal: controller.signal }).then(setSources).catch(cause => { if (!controller.signal.aborted) setError(problem(cause)); });
    return () => controller.abort();
  }, [creating, kind, sourcePage, permissions, revision]);
  useEffect(() => () => { detailRevision.current += 1; }, []);

  async function open(id: string) {
    const current = ++detailRevision.current;
    setError("");
    try { const result = await apiClient.request<Claim>(`/api/v1/supplier-claims/${id}`); if (current === detailRevision.current) setDetail(result); }
    catch (cause) { if (current === detailRevision.current) setError(problem(cause)); }
  }

  async function mutate(path: string, values: Record<string, unknown>) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(values);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      const result = await apiClient.request<Claim>(`/api/v1/supplier-claims${path}`, { method: "POST", headers: { "Idempotency-Key": key }, body });
      detailRevision.current += 1;
      setDetail(result);
      setCreating(false);
      setRevision(value => value + 1);
      setNotice("Operación registrada. El estado refleja la compensación efectivamente recibida o aplicada.");
      onChanged?.();
    } catch (cause) { setError(problem(cause)); if (detail && !creating) await open(detail.id); }
    finally { sending.current = false; setBusy(false); }
  }

  function submit(event: FormEvent<HTMLFormElement>, action: string) {
    event.preventDefault();
    if (!detail) return;
    const values: Record<string, unknown> = Object.fromEntries(new FormData(event.currentTarget));
    if (action === "acknowledge") values.agreed_amount = values.agreed_amount || null;
    if (action === "replacement-orders") {
      values.items = detail.items.map(item => ({ product_id: item.product_id, quantity: values[`quantity_${item.product_id}`] })).filter(item => Number(item.quantity) > 0);
      detail.items.forEach(item => { delete values[`quantity_${item.product_id}`]; });
      if (!(values.items as unknown[]).length) { setError("Indica al menos una unidad pendiente para la reposición."); return; }
    }
    const target = action === "change" ? String(values.action) : action;
    delete values.action;
    void mutate(`/${detail.id}/${target}`, { ...values, version: detail.version });
  }

  return <section className="space-y-4 rounded-xl border bg-white p-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Reclamos y compensaciones de proveedores</h2><p className="text-sm text-slate-500">Acuerdos, créditos aplicados y reposiciones aceptadas con historial.</p></div><div className="flex gap-2"><button type="button" className={button} disabled={busy} onClick={() => { setRevision(value => value + 1); if (detail) void open(detail.id); }}>Actualizar</button>{write && permissions.includes("purchases:read") && <button type="button" className={button} disabled={busy} onClick={() => { setCreating(value => !value); setError(""); }}>Nuevo reclamo</button>}</div></div>
    {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}
    {creating && <form className="space-y-3 rounded-xl border p-4" onSubmit={event => { event.preventDefault(); if (!source) return; const values = Object.fromEntries(new FormData(event.currentTarget)); const items = source.lines.map(item => ({ product_id: item.product_id, quantity: quantities[item.product_id] || "0" })).filter(item => Number(item.quantity) > 0); if (!items.length) { setError("Selecciona las cantidades que reclamas."); return; } void mutate("", { ...values, expected_amount: values.expected_amount || null, source_kind: kind, source_id: sourceId, items }); }}>
      <h3 className="font-medium">Origen del reclamo</h3><p className="text-sm text-slate-500">Para faltantes de compra, cancela primero las unidades no entregadas en el control de saldos. Calidad y devoluciones se documentan desde la recepción o devolución; los sobreprecios, desde la factura conciliada.</p><label className="flex flex-col gap-1 text-sm">Tipo de documento<select className={field} value={kind} disabled={busy} onChange={event => { setKind(event.target.value); setSourcePage(0); }}>{Object.entries(kinds).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="flex flex-col gap-1 text-sm">Documento y proveedor<select className={field} value={sourceId} required disabled={busy} onChange={event => { setSourceId(event.target.value); setQuantities({}); }}><option value="">Seleccionar documento</option>{sources.items.map(item => <option key={item.source_id} value={item.source_id}>{item.label} · {item.supplier_name} · {item.currency}</option>)}</select></label>
      <div className="flex items-center gap-2 text-sm"><button type="button" className={button} disabled={sourcePage === 0 || busy} onClick={() => setSourcePage(value => value - 1)}>Documentos anteriores</button><span>Página {sourcePage + 1}</span><button type="button" className={button} disabled={(sourcePage + 1) * 20 >= sources.total_count || busy} onClick={() => setSourcePage(value => value + 1)}>Documentos siguientes</button></div>
      {source?.lines.map(item => <label key={item.product_id} className="flex flex-wrap items-center justify-between gap-2 text-sm">{item.name} · {item.sku} · Origen: {item.quantity} · Pendiente: {item.pending_quantity}{kind === "purchase_order" && <> · Faltante cancelado reclamable: {item.shortage_claimable_quantity}</>}<input aria-label={`Cantidad reclamada de ${item.name}`} className={field} type="number" min="0" max={kind === "purchase_order" ? item.shortage_claimable_quantity : item.quantity} step="0.000001" value={quantities[item.product_id] || ""} disabled={busy} onChange={event => setQuantities(previous => ({ ...previous, [item.product_id]: event.target.value }))} /></label>)}
      <label className="flex flex-col gap-1 text-sm">Motivo<select name="reason_type" className={field}>{Object.entries(reasons).filter(([value]) => kind === "purchase_order" ? value === "shortage" : kind === "invoice_match" ? value === "overprice" : value !== "overprice").map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="flex flex-col gap-1 text-sm">Compensación solicitada<select name="resolution" className={field}>{Object.entries(resolutions).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="flex flex-col gap-1 text-sm">Importe reclamado {source?.currency} (vacío: valor de las unidades)<input name="expected_amount" className={field} type="number" min="0" step="0.000001" /></label>
      <label className="flex flex-col gap-1 text-sm">Descripción y sustento<textarea name="description" className={field} required minLength={5} maxLength={4000} /></label><button className={button} disabled={busy || !source}>Registrar reclamo</button>
    </form>}
    <label className="flex flex-col gap-1 text-sm">Filtrar por estado<select className={field} value={status} disabled={busy} onChange={event => { setStatus(event.target.value); setPage(0); }}><option value="">Todos los estados</option>{Object.entries(states).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Reclamo</th><th className="p-2">Proveedor</th><th className="p-2">Estado</th><th className="p-2">Acuerdo</th><th className="p-2">Detalle</th></tr></thead><tbody>{rows.items.map(item => <tr key={item.id} className="border-t"><td className="p-2">{item.code}</td><td className="p-2">{item.supplier_name}</td><td className="p-2">{states[item.status] || item.status}</td><td className="p-2">{resolutions[item.resolution]} · {item.currency} {item.agreed_amount || item.expected_amount}</td><td className="p-2"><button className={button} disabled={busy} onClick={() => void open(item.id)}>Abrir</button></td></tr>)}</tbody></table>{!rows.items.length && <p className="p-3 text-sm text-slate-500">No hay reclamos en esta página.</p>}</div>
    <div className="flex items-center gap-3 text-sm"><button className={button} disabled={page === 0 || busy} onClick={() => setPage(value => value - 1)}>Anterior</button><span>{rows.total_count} reclamos · Página {page + 1}</span><button className={button} disabled={(page + 1) * 10 >= rows.total_count || busy} onClick={() => setPage(value => value + 1)}>Siguiente</button></div>
    {detail && <div className="space-y-4 rounded-xl border p-4" key={`${detail.id}:${detail.version}`}><div className="flex justify-between gap-2"><h3 className="font-semibold">{detail.code} · {detail.supplier_name}</h3><button className={button} disabled={busy} onClick={() => { detailRevision.current += 1; setDetail(null); }}>Cerrar detalle</button></div>
      <p className="text-sm">{states[detail.status]} · {reasons[detail.reason_type]} · {resolutions[detail.resolution]}</p><p className="text-sm">{detail.description}</p><p className="break-all text-xs text-slate-500">{kinds[detail.source_kind]}: {detail.source_id} · Compra: {detail.purchase_order_id}</p>
      {detail.resolution !== "replacement" && <p className="rounded-lg bg-slate-50 p-3 text-sm">{detail.currency} · Reclamado: {detail.expected_amount} · Acordado: {detail.agreed_amount || "Pendiente"} · Crédito emitido: {detail.credits.issued} · Disponible: {detail.credits.available} · Aplicado o reintegrado: {detail.credits.applied}</p>}
      <ul className="space-y-2 text-sm">{detail.items.map(item => <li key={item.product_id}>{item.name} · {item.sku} · Reclamado: {item.quantity}{detail.resolution === "replacement" && <> · Recibido y aceptado: {item.replacement_received} · Comprometido: {item.replacement_committed} · Disponible para nueva orden: {item.replacement_available}</>}</li>)}</ul>
      {write && detail.status === "open" && <form className="grid gap-3 rounded-lg border p-3" onSubmit={event => submit(event, "acknowledge")}><h4 className="font-medium">Registrar acuerdo del proveedor</h4><label className="flex flex-col gap-1 text-sm">Resolución<select className={field} name="resolution" defaultValue={detail.resolution}>{Object.entries(resolutions).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="flex flex-col gap-1 text-sm">Importe acordado (para crédito o descuento)<input className={field} name="agreed_amount" type="number" min="0" max={detail.expected_amount} step="0.000001" defaultValue={detail.resolution === "replacement" ? "" : detail.expected_amount} /></label><textarea aria-label="Sustento del acuerdo" className={field} name="notes" required minLength={5} maxLength={4000} placeholder="Sustento del acuerdo" /><button className={button} disabled={busy}>Registrar acuerdo</button></form>}
      {permissions.includes("payments:write") && detail.resolution !== "replacement" && ["acknowledged", "credit_available", "partially_compensated"].includes(detail.status) && Number(detail.credits.issued) < Number(detail.agreed_amount) && <form className="grid gap-3 rounded-lg border p-3" onSubmit={event => submit(event, "credits")}><h4 className="font-medium">Registrar documento compensatorio</h4><label className="flex flex-col gap-1 text-sm">Importe {detail.currency}<input name="amount" className={field} required type="number" min="0.000001" max={Math.max(0, Number(detail.agreed_amount) - Number(detail.credits.issued))} step="0.000001" /></label><label className="flex flex-col gap-1 text-sm">Fecha del documento<input className={field} name="movement_date" type="date" required max={detail.business_date} defaultValue={detail.business_date} /></label><label className="flex flex-col gap-1 text-sm">Referencia única del proveedor<input className={field} name="reference" required maxLength={128} /></label><textarea aria-label="Sustento del crédito" className={field} name="notes" required minLength={5} maxLength={4000} placeholder="Sustento del crédito" /><p className="text-sm text-slate-500">El crédito quedará disponible en Finanzas para aplicarlo a una obligación o registrar su reintegro. Esa operación actualizará el reclamo.</p><button className={button} disabled={busy}>Registrar crédito</button></form>}
      {canReplace && detail.resolution === "replacement" && ["acknowledged", "partially_compensated"].includes(detail.status) && detail.items.some(item => Number(item.replacement_available) > 0) && <form className="grid gap-3 rounded-lg border p-3" onSubmit={event => submit(event, "replacement-orders")}><h4 className="font-medium">Ordenar reposición</h4>{detail.items.filter(item => Number(item.replacement_available) > 0).map(item => <label key={item.product_id} className="flex flex-col gap-1 text-sm">{item.name} · Disponible: {item.replacement_available}<input className={field} type="number" name={`quantity_${item.product_id}`} min="0" max={item.replacement_available} step="0.000001" defaultValue={item.replacement_available} /></label>)}<label className="flex flex-col gap-1 text-sm">Entrega acordada<input className={field} name="delivery_date" type="date" required min={detail.business_date} defaultValue={detail.business_date} /></label><textarea aria-label="Sustento de la reposición" className={field} name="notes" required minLength={5} maxLength={4000} placeholder="Sustento de la reposición" /><p className="text-sm text-slate-500">Se crea una orden aprobada sin nueva deuda. Registra su recepción e inspección en Compras para actualizar el cumplimiento.</p><button className={button} disabled={busy}>Autorizar orden de reposición</button></form>}
      {write && ["open", "acknowledged", "cancelled", "rejected"].includes(detail.status) && <form className="flex flex-wrap gap-2" onSubmit={event => submit(event, "change")}><select aria-label="Acción sobre el reclamo" name="action" className={field}>{["cancelled", "rejected"].includes(detail.status) ? <option value="reopen">Reabrir</option> : <><option value="cancel">Cancelar sin compensación</option>{detail.status === "open" && <option value="reject">Rechazar</option>}</>}</select><input className={`${field} grow`} name="reason" required minLength={5} maxLength={4000} placeholder="Motivo de la transición" aria-label="Motivo de la transición" /><button className={button} disabled={busy}>Aplicar transición</button></form>}
      {!!detail.credit_documents.length && <div><h4 className="font-medium">Documentos de crédito</h4><ul className="text-sm">{detail.credit_documents.map(item => <li key={item.id}>{item.date} · {item.reference} · {detail.currency} {item.amount}</li>)}</ul></div>}
      {!!detail.replacement_orders.length && <div><h4 className="font-medium">Órdenes de reposición</h4><ul className="text-sm">{detail.replacement_orders.map(item => <li key={item.id}>Compra {item.id.substring(0, 8).toUpperCase()} · {item.status}</li>)}</ul></div>}
      <details><summary className="cursor-pointer text-sm font-medium">Historial del reclamo</summary><ul className="mt-2 space-y-2 text-sm">{detail.history.map((item, index) => <li key={`${item.at}:${index}`}>{new Date(item.at).toLocaleString("es-PE")} · {actions[item.action] || item.action} · {item.actor}<p>{item.notes}</p></li>)}</ul></details>
    </div>}
  </section>;
}
