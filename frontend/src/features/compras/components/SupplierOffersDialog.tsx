import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";

interface Supplier extends Record<string, unknown> { id: string; legal_name: string; tax_id: string }
interface Line { product_id: string; quantity: string; unit_cost: string; name?: string; sku?: string }
interface Offer { id: string; version: number; supplier_name: string; can_select: boolean; lowest_in_currency: boolean; selection_errors: string[]; status: string; details: { supplier_reference: string; currency: string; total_with_shipping: string; shipping_cost: string; lead_time_days: number; warranty_months: number; valid_until: string; notes: string } }
interface Comparison { requisition: { status: string; lines: Line[] }; offers: Offer[]; comparison_rule: string }
interface LineValues { unit_cost: string; tax_rate: string; minimum_quantity: string; order_multiple: string }

export function SupplierOffersDialog({ requisitionId, canWrite, onClose, onChanged }: { requisitionId: string; canWrite: boolean; onClose: () => void; onChanged: () => void }) {
  const [data, setData] = useState<Comparison | null>(null);
  const [supplier, setSupplier] = useState<Supplier>();
  const [values, setValues] = useState<Record<string, LineValues>>({});
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const sending = useRef(false);
  const keys = useRef(new Map<string, string>());
  const revision = useRef(0);
  const input = "mt-1 w-full rounded-lg border bg-white p-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() {
    const requested = ++revision.current;
    const result = await apiClient.request<Comparison>(`/api/v1/purchase-requisitions/${requisitionId}/supplier-offers`);
    if (requested !== revision.current) return;
    setData(result);
    setValues(Object.fromEntries(result.requisition.lines.map(line => [line.product_id, { unit_cost: line.unit_cost, tax_rate: "0", minimum_quantity: "1", order_multiple: "1" }])));
  }

  useEffect(() => { void load().catch(() => setError("No se pudieron cargar las ofertas.")); return () => { revision.current += 1; }; }, [requisitionId]);

  async function write(path: string, payload: unknown, message: string) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = keys.current.get(signature) || crypto.randomUUID();
    keys.current.set(signature, key);
    try {
      await apiClient.request(path, { method: "POST", headers: { "Idempotency-Key": key }, body });
      keys.current.delete(signature);
      setNotice(message);
      await load();
      onChanged();
    } catch (cause) { const detail = (cause as { detail?: unknown }).detail; setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo registrar la operación."); }
    finally { sending.current = false; setBusy(false); }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supplier || !data) return;
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    void write(`/api/v1/purchase-requisitions/${requisitionId}/supplier-offers`, { ...fields, supplier_id: supplier.id, lead_time_days: Number(fields.lead_time_days), warranty_months: Number(fields.warranty_months), payment_terms_days: Number(fields.payment_terms_days), items: data.requisition.lines.map(line => ({ product_id: line.product_id, quantity: line.quantity, ...values[line.product_id], discount_percentage: "0" })) }, "Oferta registrada y disponible para comparación.");
  }

  function change(id: string, field: keyof LineValues, value: string) { setValues(previous => ({ ...previous, [id]: { ...previous[id], [field]: value } })); }

  return <ModalSurface labelledBy="supplier-offers-title" blocked={busy} onClose={onClose}><section className="app-modal-panel max-h-[90vh] w-full max-w-5xl space-y-4 overflow-y-auto rounded-2xl bg-white p-5 text-slate-900"><header className="flex justify-between gap-3"><h2 id="supplier-offers-title" className="text-lg font-semibold">Comparación de ofertas de proveedores</h2><button type="button" className={button} disabled={busy} onClick={onClose}>Cerrar</button></header>{error && <p role="alert" className="text-sm text-red-700">{error}</p>}{notice && <p role="status" className="text-sm text-teal-800">{notice}</p>}{data && <><p className="text-sm text-slate-500">{data.comparison_rule}</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Proveedor / referencia</th><th className="p-2">Total con flete</th><th className="p-2">Plazo</th><th className="p-2">Garantía</th><th className="p-2">Vigencia / estado</th><th className="p-2">Elegir</th></tr></thead><tbody>{data.offers.map(offer => <tr key={offer.id} className="border-t"><td className="p-2">{offer.supplier_name}<strong className="block">{offer.details.supplier_reference}</strong>{offer.selection_errors.map(message => <p key={message} className="text-xs text-amber-800">{message}</p>)}</td><td className="p-2">{offer.details.currency} {offer.details.total_with_shipping}{offer.lowest_in_currency && <span className="block text-xs text-teal-700">Menor importe en esta moneda</span>}</td><td className="p-2">{offer.details.lead_time_days} días</td><td className="p-2">{offer.details.warranty_months} meses</td><td className="p-2">{offer.details.valid_until}<span className="block">{offer.status}</span></td><td className="p-2">{canWrite && <button type="button" className={button} disabled={busy || !offer.can_select || reason.trim().length < 5} onClick={() => void write(`/api/v1/supplier-offers/${offer.id}/select`, { version: offer.version, reason }, "Oferta seleccionada. Se generó una orden pendiente de aprobación y se conservó la comparación.")}>Seleccionar y generar orden</button>}</td></tr>)}</tbody></table></div>{canWrite && <label className="block text-sm">Justificación de la elección<textarea className={input} value={reason} onChange={event => setReason(event.target.value)} minLength={5} maxLength={2000} placeholder="Explica la elección considerando costo, plazo, garantía y condiciones." /></label>}{canWrite && data.requisition.status === "approved" && <form onSubmit={submit} className="space-y-4 border-t pt-4"><h3 className="font-semibold">Registrar una oferta recibida</h3><fieldset disabled={busy} className="space-y-4"><RemoteEntitySelect<Supplier> value={supplier?.id || ""} initialOption={supplier ? { value: supplier.id, label: supplier.legal_name, description: supplier.tax_id, data: supplier } : undefined} onChange={(_, option) => setSupplier(option?.data)} endpoint="/api/v1/suppliers" entityType="supplier" mapOption={item => ({ value: item.id, label: item.legal_name, description: item.tax_id, data: item })} label="Proveedor" /><div className="grid gap-3 sm:grid-cols-4"><label className="text-sm">Referencia<input className={input} name="supplier_reference" required maxLength={128} /></label><label className="text-sm">Moneda<input className={input} name="currency" required pattern="[A-Z]{3}" maxLength={3} defaultValue="PEN" /></label><label className="text-sm">Válida hasta<input className={input} name="valid_until" type="date" required /></label><label className="text-sm">Plazo de entrega en días<input className={input} name="lead_time_days" type="number" min="0" max="3650" required defaultValue="7" /></label><label className="text-sm">Garantía en meses<input className={input} name="warranty_months" type="number" min="0" max="1200" required defaultValue="0" /></label><label className="text-sm">Flete acordado<input className={input} name="shipping_cost" type="number" min="0" step="0.000001" required defaultValue="0" /></label><label className="text-sm">Pago en días<input className={input} name="payment_terms_days" type="number" min="0" max="365" required defaultValue="30" /></label><label className="text-sm">Condiciones y notas<input className={input} name="notes" maxLength={4000} /></label></div><div className="space-y-3">{data.requisition.lines.map(line => <div key={line.product_id} className="flex flex-wrap items-end gap-3 rounded-lg border p-3"><strong className="mr-auto text-sm">{line.sku} · {line.name || line.product_id} · Cantidad: {line.quantity}</strong>{([['unit_cost', 'Costo neto', '0'], ['tax_rate', 'Impuesto (0–1)', '0'], ['minimum_quantity', 'Mínimo de compra', '0.000001'], ['order_multiple', 'Múltiplo', '0.000001']] as const).map(([field, label, minimum]) => <label className="w-32 text-xs" key={field}>{label}<input className={input} type="number" min={minimum} max={field === "tax_rate" ? "1" : undefined} step="0.000001" required value={values[line.product_id]?.[field] || "0"} onChange={event => change(line.product_id, field, event.target.value)} /></label>)}</div>)}</div><button type="submit" disabled={busy || !supplier} className={button}>Registrar oferta</button></fieldset></form>}</>}</section></ModalSurface>;
}
