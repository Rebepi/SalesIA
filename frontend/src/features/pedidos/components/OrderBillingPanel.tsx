import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";

interface BillingLine {
  order_line_number: number;
  sku: string;
  product_name?: string;
  billable_quantity: string;
  billed_quantity: string;
}

interface BillingData {
  currency: string;
  lines: BillingLine[];
  sales: Array<{ sale_id: string; number: string; status: string; fulfillment_status: string; total: string }>;
}

export function OrderBillingPanel({ orderId, canWrite }: { orderId: string; canWrite: boolean }) {
  const [data, setData] = useState<BillingData | null>(null);
  const [quantities, setQuantities] = useState<Record<number, string>>({});
  const [documentType, setDocumentType] = useState<"INVOICE" | "RECEIPT">("RECEIPT");
  const [isCredit, setIsCredit] = useState(false);
  const [exchangeRate, setExchangeRate] = useState("1");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const sending = useRef(false);
  const activeOrder = useRef(orderId);
  activeOrder.current = orderId;
  const attempt = useRef({ signature: "", key: "" });

  async function load() {
    const result = await apiClient.request<BillingData>(`/api/v1/orders/${orderId}/billing`);
    if (activeOrder.current !== orderId) return;
    setData(result);
    setQuantities(Object.fromEntries(result.lines.map(line => [line.order_line_number, "0"])));
  }

  useEffect(() => {
    setData(null);
    setError("");
    setMessage("");
    void load().catch(() => setError("No se pudo consultar la facturación del pedido."));
  }, [orderId]);

  async function createInvoice() {
    if (sending.current || !data) return;
    sending.current = true;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const selected = data.lines.filter(line => Number(quantities[line.order_line_number] || 0) > 0);
      if (!selected.length) throw new Error("Selecciona al menos una cantidad para facturar.");
      const body = JSON.stringify({ document_type: documentType, is_credit: isCredit, exchange_rate: exchangeRate, lines: selected.map(line => ({ order_line_number: line.order_line_number, quantity: quantities[line.order_line_number] })) });
      const signature = `${orderId}:${body}`;
      if (attempt.current.signature !== signature) attempt.current = { signature, key: crypto.randomUUID() };
      await apiClient.request(`/api/v1/orders/${orderId}/billing`, { method: "POST", headers: { "Idempotency-Key": attempt.current.key }, body });
      attempt.current = { signature: "", key: "" };
      setMessage("Venta en borrador creada. Ábrela en Ventas para revisar las condiciones y confirmar; el despacho se gestiona desde el pedido.");
      await load();
    } catch (cause) {
      const detail = cause as { detail?: unknown; message?: string };
      setError(typeof detail.detail === "string" ? detail.detail : detail.message || "No se pudo generar la venta.");
    } finally {
      sending.current = false;
      setBusy(false);
    }
  }

  return <section className="space-y-3 rounded-2xl border border-slate-200 p-4"><h4 className="font-bold">Facturación vinculada al pedido</h4><p>Las ventas conservan las condiciones del pedido. Las cantidades comprometidas en borradores también reducen el saldo facturable.</p>{error && <p role="alert" className="text-red-700">{error}</p>}{message && <p role="status" className="text-emerald-700">{message}</p>}{data && <><ul className="space-y-2">{data.sales.map(sale => <li key={sale.sale_id} className="rounded-lg bg-slate-50 p-2">{sale.number} · {sale.status} · Entrega: {sale.fulfillment_status} · {data.currency} {sale.total}</li>)}</ul>{canWrite && <><div className="space-y-2">{data.lines.map(line => <label key={line.order_line_number} className="flex items-center justify-between gap-3"><span>{line.sku} · Por facturar: {line.billable_quantity}</span><input aria-label={`Facturar línea ${line.order_line_number}`} type="number" min="0" step="any" max={line.billable_quantity} disabled={busy || Number(line.billable_quantity) <= 0} value={quantities[line.order_line_number] || "0"} onChange={event => setQuantities(previous => ({ ...previous, [line.order_line_number]: event.target.value }))} className="w-24 rounded-lg border p-2" /></label>)}</div><div className="flex flex-wrap items-center gap-3"><select aria-label="Tipo de documento" value={documentType} onChange={event => setDocumentType(event.target.value as "INVOICE" | "RECEIPT")} className="rounded-lg border p-2"><option value="RECEIPT">Boleta</option><option value="INVOICE">Factura</option></select><label className="flex items-center gap-2"><input type="checkbox" checked={isCredit} onChange={event => setIsCredit(event.target.checked)} />A crédito</label><label>Tipo de cambio <input type="number" min="0.000001" step="any" value={exchangeRate} onChange={event => setExchangeRate(event.target.value)} className="w-24 rounded-lg border p-2" /></label><button type="button" disabled={busy} onClick={() => void createInvoice()} className="rounded-lg bg-teal-700 px-3 py-2 text-white disabled:opacity-50">{busy ? "Creando…" : "Crear venta en borrador"}</button></div></>}</>}</section>;
}
