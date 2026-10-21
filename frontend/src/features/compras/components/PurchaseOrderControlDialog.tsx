import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";

interface Line { product_id: string; quantity: string; unit_cost: string; processed_quantity: string; cancelled_quantity: string; pending_quantity: string; sku?: string; name?: string }
interface Order { id: string; version: number; status: string; lines: Line[]; details: { currency?: string; payment_terms_days?: number; delivery_date?: string; notes?: string; commercial_lines?: { product_id: string; unit_list_cost: string; tax_rate: string; discount_percentage: string }[] } }
interface Revision { id: string; version: number; action: string; reason: string; actor: string; created_at: string; snapshot: Order }
interface EditLine { quantity: string; unit_cost: string; tax_rate: string; discount_percentage: string; cancel: string }

export function PurchaseOrderControlDialog({ orderId, canWrite, onClose, onChanged }: { orderId: string; canWrite: boolean; onClose: () => void; onChanged: () => void }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [versions, setVersions] = useState<Revision[]>([]);
  const [selectedVersion, setSelectedVersion] = useState(0);
  const [names, setNames] = useState<Record<string, { sku: string; name: string }>>({});
  const [action, setAction] = useState("cancel_lines");
  const [rows, setRows] = useState<Record<string, EditLine>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const revision = useRef(0);
  const input = "mt-1 w-full rounded-lg border bg-white p-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() {
    const requested = ++revision.current;
    const [current, history, context] = await Promise.all([apiClient.request<Order>(`/api/v1/purchase-orders/${orderId}`), apiClient.request<Revision[]>(`/api/v1/purchase-orders/${orderId}/versions`), apiClient.request<{ lines: { product_id: string; sku: string; name: string }[] }>(`/api/v1/purchase-orders/${orderId}/invoice-context`)]);
    if (requested !== revision.current) return;
    setOrder(current);
    setVersions(history);
    setNames(Object.fromEntries(context.lines.map(line => [line.product_id, { sku: line.sku, name: line.name }])));
    setRows(Object.fromEntries(current.lines.map(line => {
      const commercial = current.details.commercial_lines?.find(item => item.product_id === line.product_id);
      return [line.product_id, { quantity: line.quantity, unit_cost: commercial?.unit_list_cost || line.unit_cost, tax_rate: commercial?.tax_rate || "0", discount_percentage: commercial?.discount_percentage || "0", cancel: "0" }];
    })));
  }

  useEffect(() => { void load().catch(() => setError("No se pudo cargar la orden y su historial.")); return () => { revision.current += 1; }; }, [orderId]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!order || sending.current) return;
    const values = Object.fromEntries(new FormData(event.currentTarget)) as Record<string, string>;
    const path = action === "edit" ? `/api/v1/purchase-orders/${orderId}` : `/api/v1/purchase-orders/${orderId}/balance-action`;
    const payload = action === "edit" ? { version: order.version, reason: values.reason, currency: values.currency, payment_terms_days: Number(values.payment_terms_days), delivery_date: values.delivery_date ? `${values.delivery_date}T12:00:00Z` : null, notes: values.notes, items: order.lines.map(line => ({ product_id: line.product_id, quantity: rows[line.product_id].quantity, unit_cost: rows[line.product_id].unit_cost, tax_rate: rows[line.product_id].tax_rate, discount_percentage: rows[line.product_id].discount_percentage })) } : { version: order.version, reason: values.reason, action, items: action === "cancel_lines" ? order.lines.filter(line => Number(rows[line.product_id]?.cancel || 0) > 0).map(line => ({ product_id: line.product_id, quantity: rows[line.product_id].cancel })) : [] };
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    sending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await apiClient.request(path, { method: action === "edit" ? "PUT" : "POST", body, headers: { "Idempotency-Key": key } });
      keys.current.delete(signature);
      setNotice(action === "reopen" || action === "edit" ? "Orden actualizada. Revisa su estado de aprobación antes de recibir." : "Saldo actualizado. Las cantidades canceladas ya no se consideran en reposición.");
      await load();
      onChanged();
    } catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo actualizar la orden."); }
    finally { sending.current = false; setBusy(false); }
  }

  function change(id: string, field: keyof EditLine, value: string) { setRows(previous => ({ ...previous, [id]: { ...previous[id], [field]: value } })); }
  const historical = versions.find(item => item.version === selectedVersion);
  const display = historical?.snapshot || order;

  return <ModalSurface labelledBy="purchase-control-title" blocked={busy} onClose={onClose}><section className="app-modal-panel max-h-[90vh] w-full max-w-5xl space-y-4 overflow-y-auto rounded-2xl bg-white p-5 text-slate-900"><header className="flex justify-between gap-3"><h2 id="purchase-control-title" className="text-lg font-semibold">Revisión, saldos e historial de compra</h2><button type="button" className={button} disabled={busy} onClick={onClose}>Cerrar</button></header>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{order && <><p className="text-sm">Estado actual: {order.status} · Versión {order.version}. Las unidades recibidas se conservan y se corrigen mediante recepción o devolución.</p><label className="block text-sm">Consultar versión<select className={input} value={selectedVersion} onChange={event => setSelectedVersion(Number(event.target.value))}><option value={0}>Valores actuales</option>{versions.map(item => <option key={item.id} value={item.version}>v{item.version} · {item.action} · {item.actor}</option>)}</select></label>{historical && <p className="text-sm text-slate-600">{historical.reason} · {new Date(historical.created_at).toLocaleString("es-PE")}</p>}<div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Producto</th><th className="p-2">Pedida</th><th className="p-2">Recibida</th><th className="p-2">Cancelada</th><th className="p-2">Pendiente</th><th className="p-2">Costo neto</th></tr></thead><tbody>{display?.lines.map(line => <tr key={line.product_id} className="border-t"><td className="p-2">{line.sku || names[line.product_id]?.sku}<strong className="block">{line.name || names[line.product_id]?.name || "Producto"}</strong></td><td className="p-2">{line.quantity}</td><td className="p-2">{line.processed_quantity}</td><td className="p-2">{line.cancelled_quantity || "0"}</td><td className="p-2">{line.pending_quantity}</td><td className="p-2">{display.details.currency} {line.unit_cost}</td></tr>)}</tbody></table></div>{canWrite && <form key={`${order.version}:${action}`} onSubmit={event => void submit(event)} className="space-y-4 border-t pt-4"><fieldset disabled={busy} className="space-y-4"><label className="block text-sm">Acción<select className={input} value={action} onChange={event => setAction(event.target.value)}><option value="cancel_lines">Cancelar cantidades pendientes por producto</option><option value="close_short">Cerrar todo el saldo pendiente</option><option value="reopen">Reabrir el saldo del último cierre</option><option value="edit" disabled={["partially_received", "received", "closed", "cancelled"].includes(order.status)}>Corregir orden sin recepciones</option></select></label>{action === "edit" && <div className="grid gap-3 sm:grid-cols-4"><label className="text-sm">Moneda<input className={input} name="currency" pattern="[A-Z]{3}" maxLength={3} required defaultValue={order.details.currency || "USD"} /></label><label className="text-sm">Plazo de pago<input className={input} name="payment_terms_days" type="number" min="0" max="365" required defaultValue={order.details.payment_terms_days ?? 30} /></label><label className="text-sm">Entrega estimada<input className={input} name="delivery_date" type="date" defaultValue={order.details.delivery_date?.slice(0, 10) || ""} /></label><label className="text-sm">Notas<input className={input} name="notes" maxLength={1000} defaultValue={order.details.notes || ""} /></label></div>}{["edit", "cancel_lines"].includes(action) && <div className="space-y-2">{order.lines.map(line => <div key={line.product_id} className="flex flex-wrap items-end gap-3 rounded-lg border p-3"><strong className="mr-auto text-sm">{names[line.product_id]?.sku} · {names[line.product_id]?.name}</strong>{action === "cancel_lines" ? <label className="text-xs">Cancelar hasta {line.pending_quantity}<input className={input} type="number" min="0" max={line.pending_quantity} step="0.000001" value={rows[line.product_id]?.cancel || "0"} onChange={event => change(line.product_id, "cancel", event.target.value)} /></label> : <>{([['quantity', 'Cantidad'], ['unit_cost', 'Costo de lista'], ['discount_percentage', 'Descuento %'], ['tax_rate', 'Impuesto (0–1)']] as const).map(([field, label]) => <label key={field} className="w-32 text-xs">{label}<input className={input} required type="number" min={field === "quantity" ? "0.000001" : "0"} max={field === "tax_rate" ? "1" : field === "discount_percentage" ? "100" : undefined} step="0.000001" value={rows[line.product_id]?.[field] || "0"} onChange={event => change(line.product_id, field, event.target.value)} /></label>)}</>}</div>)}</div>}<label className="block text-sm">Motivo<input className={input} name="reason" required minLength={5} maxLength={2000} /></label><p className="text-xs text-slate-500">Una reapertura recupera únicamente las unidades del último cierre corto y vuelve a requerir aprobación. Las cancelaciones anteriores permanecen registradas.</p><button type="submit" disabled={busy} className={button}>{busy ? "Guardando…" : "Registrar cambio"}</button></fieldset></form>}</>}</section></ModalSurface>;
}
