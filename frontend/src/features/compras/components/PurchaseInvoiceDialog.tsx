import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import { ModalSurface } from "../../../ui/components/ModalSurface";

interface InvoiceLine { product_id: string; sku: string; name: string; ordered_quantity: string; accepted_quantity: string; committed_invoice_quantity: string; invoiceable_quantity: string; unit_price: string; tax_rate: string }
interface Match { id: string; status: string; invoice_number: string; invoice_amount: string; currency: string; version: number; payable_id: string | null; payable_status: string | null; validation: { errors?: Array<{ code: string; message: string; product_id?: string }> }; lines: unknown[] }
interface Context { supplier_id: string; business_date: string; order_id: string; currency: string; status: string; payment_terms_days: number; lines: InvoiceLine[]; matches: Match[]; legacy_matches_requiring_review: string[]; policy: { unit_price_tolerance_percentage: string; rounding_tolerance: string } }
interface LineInput { quantity: string; price: string; tax: string }

export function PurchaseInvoiceDialog({ orderId, canWrite, onClose, onChanged }: { orderId: string; canWrite: boolean; onClose: () => void; onChanged: () => void }) {
  const [context, setContext] = useState<Context | null>(null);
  const [lines, setLines] = useState<Record<string, LineInput>>({});
  const [permissions, setPermissions] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reason, setReason] = useState("");
  const [payableMatch, setPayableMatch] = useState<Match | null>(null);
  const sending = useRef(false);
  const attempts = useRef(new Map<string, string>());
  const sequence = useRef(0);
  const input = "mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm";
  const button = "rounded-lg border px-3 py-2 text-sm disabled:opacity-50";

  async function load() {
    const current = ++sequence.current;
    const result = await apiClient.request<Context>(`/api/v1/purchase-orders/${orderId}/invoice-context`);
    if (current !== sequence.current) return;
    setContext(result);
    setLines(Object.fromEntries(result.lines.map(line => [line.product_id, { quantity: "0", price: line.unit_price, tax: String(Number(line.tax_rate) * 100) }])));
  }

  useEffect(() => {
    void load().catch(() => setError("No se pudo cargar la recepción y facturación de la orden."));
    void apiClient.getMe().then(profile => setPermissions(profile.permissions || [])).catch(() => setPermissions([]));
    return () => { sequence.current += 1; };
  }, [orderId]);

  async function write(path: string, payload: unknown, success: string) {
    if (sending.current) return;
    sending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const body = JSON.stringify(payload);
    const signature = `${path}:${body}`;
    const key = attempts.current.get(signature) || crypto.randomUUID();
    attempts.current.set(signature, key);
    try {
      await apiClient.request(path, { method: "POST", headers: { "Idempotency-Key": key }, body });
      attempts.current.delete(signature);
      setNotice(success);
      setPayableMatch(null);
      await load();
      onChanged();
    } catch (cause) {
      const detail = (cause as { detail?: unknown }).detail;
      setError(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : "No se pudo registrar la operación.");
    } finally { sending.current = false; setBusy(false); }
  }

  const calculated = context?.lines.reduce((total, line) => { const item = lines[line.product_id]; return total + Number(item?.quantity || 0) * Number(item?.price || 0) * (1 + Number(item?.tax || 0) / 100); }, 0) || 0;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!context) return;
    const data = new FormData(event.currentTarget);
    const selected = context.lines.filter(line => Number(lines[line.product_id]?.quantity || 0) > 0);
    if (!selected.length) { setError("Selecciona las cantidades de al menos un producto."); return; }
    void write(`/api/v1/purchase-orders/${orderId}/three-way-match`, { supplier_invoice_number: data.get("invoice_number"), invoice_amount: data.get("invoice_amount") || calculated.toFixed(6), notes: data.get("notes"), invoice_lines: selected.map(line => ({ product_id: line.product_id, quantity: lines[line.product_id].quantity, unit_price: lines[line.product_id].price, tax_rate: String(Number(lines[line.product_id].tax) / 100) })) }, "Conciliación registrada. Revisa su estado y las diferencias antes de generar la obligación.");
  }

  function savePayable(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!context || !payableMatch) return;
    const values = Object.fromEntries(new FormData(event.currentTarget));
    void write("/api/v1/payables", { ...values, invoice_match_id: payableMatch.id, supplier_id: context.supplier_id, purchase_order_id: context.order_id, document_number: payableMatch.invoice_number, currency: context.currency, amount: payableMatch.invoice_amount, installments: [] }, "Obligación registrada. Sus cuotas, pagos y reversión se gestionan desde Cuentas por pagar.");
  }

  function change(productId: string, field: keyof LineInput, value: string) {
    setLines(previous => ({ ...previous, [productId]: { ...previous[productId], [field]: value } }));
  }

  return <ModalSurface labelledBy="purchase-invoice-title" blocked={busy} onClose={onClose}><section className="app-modal-panel max-h-[90vh] w-full max-w-5xl space-y-4 overflow-y-auto rounded-2xl bg-white p-5 text-slate-900"><header className="flex items-center justify-between gap-3"><h2 id="purchase-invoice-title" className="text-lg font-semibold">Orden, recepción y factura del proveedor</h2><button type="button" disabled={busy} className={button} onClick={onClose}>Cerrar</button></header>{error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="rounded-lg bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}{!context ? <p>Cargando datos de la orden…</p> : <><p className="text-sm text-slate-500">Se consideran las unidades aceptadas y las devoluciones al proveedor. Las facturas en revisión reservan sus cantidades para impedir facturación duplicada. Moneda: {context.currency}.</p><p className="text-xs text-slate-500">Tolerancia de precio: {context.policy.unit_price_tolerance_percentage}% · Redondeo del documento: {context.policy.rounding_tolerance}.</p>{context.legacy_matches_requiring_review.length > 0 && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Existen conciliaciones históricas sin detalle por producto. Revisa su respaldo y anula las que se reemplazarán antes de registrar otra factura.</p>}{canWrite && <form onSubmit={submit} className="space-y-4"><fieldset disabled={busy} className="space-y-4"><div className="grid gap-3 sm:grid-cols-3"><label className="text-sm">Factura del proveedor<input className={input} name="invoice_number" required maxLength={64} /></label><label className="text-sm">Total con impuestos<input className={input} name="invoice_amount" type="number" min="0.000001" step="0.000001" placeholder={calculated.toFixed(6)} /><span className="text-xs text-slate-500">Vacío: usar suma de líneas {calculated.toFixed(6)}</span></label><label className="text-sm">Notas<input className={input} name="notes" maxLength={500} /></label></div><div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr><th className="p-2">Producto</th><th className="p-2">Aceptado</th><th className="p-2">Comprometido</th><th className="p-2">Por facturar</th><th className="p-2">Cantidad factura</th><th className="p-2">Precio neto</th><th className="p-2">Impuesto %</th></tr></thead><tbody>{context.lines.map(line => <tr key={line.product_id} className="border-t"><td className="p-2">{line.sku}<strong className="block">{line.name}</strong></td><td className="p-2">{line.accepted_quantity}</td><td className="p-2">{line.committed_invoice_quantity}</td><td className="p-2">{line.invoiceable_quantity}</td><td className="p-2"><input aria-label={`Facturar ${line.sku}`} className={`${input} w-24`} type="number" min="0" step="0.000001" max={line.invoiceable_quantity} value={lines[line.product_id]?.quantity || "0"} onChange={event => change(line.product_id, "quantity", event.target.value)} /></td><td className="p-2"><input aria-label={`Precio facturado ${line.sku}`} className={`${input} w-28`} type="number" min="0" step="0.000001" value={lines[line.product_id]?.price || "0"} onChange={event => change(line.product_id, "price", event.target.value)} /></td><td className="p-2"><input aria-label={`Impuesto facturado ${line.sku}`} className={`${input} w-20`} type="number" min="0" max="100" step="any" value={lines[line.product_id]?.tax || "0"} onChange={event => change(line.product_id, "tax", event.target.value)} /></td></tr>)}</tbody></table></div><button type="submit" className={button} disabled={busy || calculated <= 0}>Registrar y conciliar factura</button></fieldset></form>}<section className="space-y-3 border-t pt-4"><h3 className="font-semibold">Facturas registradas</h3>{canWrite && <label className="block text-sm">Motivo para aprobar una diferencia o anular una conciliación<textarea className={input} value={reason} minLength={5} maxLength={2000} onChange={event => setReason(event.target.value)} /></label>}{context.matches.map(match => <article className="space-y-2 rounded-xl border p-3" key={match.id}><div className="flex flex-wrap items-center justify-between gap-3"><strong>{match.invoice_number} · {match.currency || context.currency} {match.invoice_amount}</strong><span className="text-sm">{match.status} · v{match.version}</span></div>{match.validation.errors?.map((item, index) => <p key={index} className="text-sm text-amber-800">{item.message}</p>)}{match.payable_id && <p className="text-sm">Obligación vinculada: {match.payable_status}</p>}<div className="flex flex-wrap gap-2">{canWrite && match.status === "UNDER_REVIEW" && permissions.includes("approvals:manage") && <button className={button} disabled={busy || reason.trim().length < 5} type="button" onClick={() => void write(`/api/v1/purchase-invoice-matches/${match.id}/approve`, { version: match.version, reason }, "Revisión registrada con su motivo.")}>Autorizar diferencia de precio</button>}{canWrite && match.status !== "VOIDED" && (!match.payable_id || match.payable_status === "cancelled") && <button className={button} disabled={busy || reason.trim().length < 5} type="button" onClick={() => void write(`/api/v1/purchase-invoice-matches/${match.id}/void`, { version: match.version, reason }, "Conciliación anulada y cantidades liberadas.")}>Anular conciliación</button>}{!match.payable_id && ["MATCHED", "APPROVED_OVERRIDE"].includes(match.status) && match.lines.length > 0 && permissions.includes("payments:write") && <button className={button} type="button" disabled={busy} onClick={() => setPayableMatch(match)}>Generar cuenta por pagar</button>}</div></article>)}{!context.matches.length && <p className="text-sm text-slate-500">Esta orden todavía no tiene facturas conciliadas.</p>}</section>{payableMatch && <form key={payableMatch.id} onSubmit={savePayable} className="space-y-3 rounded-xl border border-teal-300 p-4"><h3 className="font-semibold">Obligación de {payableMatch.invoice_number} · {context.currency} {payableMatch.invoice_amount}</h3><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Emisión<input name="issue_date" type="date" required defaultValue={context.business_date} className={input} /></label><label className="text-sm">Vencimiento<input name="due_date" type="date" required defaultValue={new Date(new Date(`${context.business_date}T12:00:00Z`).getTime() + context.payment_terms_days * 86400000).toISOString().slice(0, 10)} className={input} /></label></div><label className="block text-sm">Notas<textarea name="notes" className={input} maxLength={4000} /></label><button className={button} disabled={busy} type="submit">Registrar obligación</button><button type="button" disabled={busy} className={`${button} ml-2`} onClick={() => setPayableMatch(null)}>Cancelar</button></form>}</>}</section></ModalSurface>;
}
