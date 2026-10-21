import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiClient } from "../../../api/client";
import type { SaleDetailData } from "../../ventas/types/SaleDetailModal";
import type { ProductItem } from "../../ventas/types/NewSalePOSModal";
import { ReturnHelp } from "./ReturnHelp";
import { returnProblem } from "../api/returnFlow";

interface Settlement {
  currency: string;
  available_amount: string;
  can_settle: boolean;
  can_grant_store_credit: boolean;
  debt_to_offset: string;
  valuation: { refundable_total: string; retained_total: string };
  warnings: string[];
  movements: { id: string; kind: string; reference_id: string; amount: string; currency: string }[];
}
interface RefundOptions {
  payment_method: string;
  currency: string;
  available_amount: string;
  returns: { id: string; available_amount: string }[];
  cash_sessions: { id: string; terminal_code: string; balance: string }[];
}
const actionLabels = { "store-credit": "Saldo a favor", "settle-debt": "Aplicar a deuda original", refund: "Reembolsar dinero", exchange: "Cambio de producto" };
const movementLabels: Record<string, string> = { store_credit: "Saldo a favor otorgado", debt_offset: "Aplicado a deuda original", refund: "Dinero reembolsado", exchange: "Aplicado a una venta de cambio" };

export function SaleReturnCompletion({ returnId, sale, warehouseId, onChanged, onOpenSale, onBusyChange }: { returnId: string; sale: SaleDetailData; warehouseId: string; onChanged: () => void; onOpenSale?: (id: string) => void; onBusyChange: (value: boolean) => void }) {
  const [data, setData] = useState<Settlement | null>(null);
  const [action, setAction] = useState<keyof typeof actionLabels>("refund");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [paymentId, setPaymentId] = useState("");
  const [options, setOptions] = useState<RefundOptions | null>(null);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [cashSessionId, setCashSessionId] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("Liquidación de devolución de venta");
  const [reference, setReference] = useState("");
  const [search, setSearch] = useState("");
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [cart, setCart] = useState<{ product: ProductItem; quantity: number }[]>([]);
  const [exchangeResult, setExchangeResult] = useState<{ exchange_sale_id: string; new_sale_total: string; return_credit_applied: string; remaining_return_value: string; difference: string } | null>(null);
  const lock = useRef(false);
  const keys = useRef(new Map<string, string>());
  const payments = (sale.payments || []).filter(item => !["RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"].includes(item.payment_method));
  const cap = Math.max(0, Math.min(Number(data?.available_amount || 0), Number(options?.returns.find(item => item.id === returnId)?.available_amount || 0)));
  const money = (value: unknown) => `${data?.currency || sale.currency} ${Number(value || 0).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setData(null); setError("");
    apiClient.request<Settlement>(`/api/v1/return-settlements/${returnId}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) { setData(result); setAmount(result.available_amount); } }).catch(cause => { if (!controller.signal.aborted) setError(returnProblem(cause)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [returnId, revision]);

  useEffect(() => {
    setOptions(null); setCashSessionId(""); setOptionsLoading(false);
    if (action !== "refund" || !paymentId) return;
    const controller = new AbortController(); setOptionsLoading(true);
    apiClient.request<RefundOptions>(`/api/v1/refund-options/${paymentId}`, { signal: controller.signal }).then(result => {
      if (controller.signal.aborted) return;
      setOptions(result); setCashSessionId(result.cash_sessions[0]?.id || "");
      setAmount(result.returns.find(item => item.id === returnId)?.available_amount || "0");
    }).catch(cause => { if (!controller.signal.aborted) setError(returnProblem(cause)); }).finally(() => { if (!controller.signal.aborted) setOptionsLoading(false); });
    return () => controller.abort();
  }, [paymentId, action, returnId, revision]);

  useEffect(() => {
    if (action !== "exchange") return;
    const controller = new AbortController(); setProductsLoading(true);
    const timer = window.setTimeout(() => {
      const query = new URLSearchParams({ warehouse_id: warehouseId, search, limit: "20", offset: "0" });
      apiClient.request<{ items: ProductItem[] }>(`/api/v1/products/search-availability?${query}`, { signal: controller.signal }).then(result => { if (!controller.signal.aborted) setProducts(result.items); }).catch(cause => { if (!controller.signal.aborted) setError(returnProblem(cause)); }).finally(() => { if (!controller.signal.aborted) setProductsLoading(false); });
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [search, action, warehouseId]);

  useEffect(() => {
    if (action === "refund" && options) setAmount(String(cap));
  }, [cap, action, options]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (lock.current || !data?.can_settle || Number(data.available_amount) <= 0) return;
    setError(""); setNotice("");
    const chosenAmount = Number(amount);
    if (action !== "exchange" && action !== "settle-debt" && (!Number.isFinite(chosenAmount) || chosenAmount <= 0 || chosenAmount > Number(data.available_amount))) { setError("El importe debe respetar el valor disponible de la devolución."); return; }
    if (action === "refund" && (!options || chosenAmount > cap || !paymentId || reference.trim().length < 3 || (options.payment_method === "CASH" && !cashSessionId))) { setError("Selecciona un pago reembolsable, la caja cuando corresponda y la referencia real del desembolso."); return; }
    if (action === "exchange" && (!cart.length || cart.some(item => !Number.isFinite(item.quantity) || item.quantity <= 0))) { setError("Selecciona los productos de reemplazo y sus cantidades."); return; }
    const path = action === "refund" ? "/api/v1/refunds" : action === "exchange" ? `/api/v1/returns/${returnId}/exchange` : `/api/v1/return-settlements/${returnId}/${action}`;
    const payload = action === "refund" ? { payment_id: paymentId, return_id: returnId, amount, reason: reason.trim(), payout_reference: reference.trim(), cash_session_id: options?.payment_method === "CASH" ? cashSessionId : null } : action === "exchange" ? { warehouse_id: warehouseId, replacement_items: cart.map(item => ({ product_id: item.product.id, quantity: String(item.quantity) })) } : { expected_available: data.available_amount, reason: reason.trim(), ...(action === "store-credit" ? { amount } : {}) };
    const body = JSON.stringify(payload); const signature = `${path}:${body}`; const key = keys.current.get(signature) || crypto.randomUUID(); keys.current.set(signature, key);
    lock.current = true; setBusy(true); onBusyChange(true);
    try {
      const result = await apiClient.request<typeof exchangeResult>(path, { method: "POST", headers: { "Idempotency-Key": key }, body });
      if (action === "exchange" && result) { setExchangeResult(result); setCart([]); }
      setNotice(action === "refund" ? "Desembolso registrado y vinculado al pago original. La salida de caja quedó registrada cuando corresponde." : action === "exchange" ? "Venta de cambio creada y valor de devolución aplicado. Revisa la diferencia y cualquier saldo restante." : "Aplicación registrada en la liquidación del cliente.");
      setRevision(value => value + 1); onChanged();
    } catch (cause) { setError(returnProblem(cause)); }
    finally { lock.current = false; setBusy(false); onBusyChange(false); }
  }
  const previousExchange = data?.movements.find(item => item.kind === "exchange")?.reference_id;
  return <section className="sales-return-workspace mt-5 space-y-4 rounded-2xl border p-5" aria-label="Liquidar devolución aceptada">
    <h3 className="font-bold">Liquidación de la devolución <ReturnHelp title="Valor disponible y aplicaciones" description="Muestra el valor disponible después de retenciones y aplicaciones. Cada reembolso, cambio o saldo a favor consume parte de ese valor para impedir que se utilice dos veces." /></h3>
    <p className="text-sm text-slate-500">El inventario se procesa al aceptar. Primero se compensa la deuda de esta venta; solo el valor restante puede usarse para saldo a favor, cambio o reembolso. Cada aplicación queda registrada.</p>
    {loading && <p role="status">Consultando valor disponible…</p>}
    {error && <div role="alert" className="text-red-600">{error}<button type="button" disabled={busy} onClick={() => setRevision(value => value + 1)}>Actualizar liquidación</button></div>}
    {notice && <p role="status" className="text-teal-600">{notice}</p>}
    {data && <>
      <div className="grid gap-3 sm:grid-cols-3">{[["Valor tras retenciones", data.valuation.refundable_total], ["Retenido", data.valuation.retained_total], ["Disponible", data.available_amount]].map(([label, value]) => <div key={label} className="rounded-xl border p-3"><p className="text-xs text-slate-500">{label}</p><strong>{money(value)}</strong></div>)}</div>
      {data.movements.map(item => <p key={item.id} className="text-sm">{movementLabels[item.kind] || item.kind}: {money(item.amount)}</p>)}
      {data.warnings.map((warning, index) => <p key={index} className="text-amber-600">{warning}</p>)}
      {(exchangeResult || previousExchange) && <div className="rounded-xl border p-4"><h4 className="font-bold">Venta de reemplazo registrada</h4>{exchangeResult && <p>Total: {money(exchangeResult.new_sale_total)} · Aplicado: {money(exchangeResult.return_credit_applied)} · Diferencia a cobrar: {money(Math.max(0, Number(exchangeResult.difference)))} · Valor restante: {money(exchangeResult.remaining_return_value)}</p>}{onOpenSale && <button type="button" disabled={busy} onClick={async () => { try { await onOpenSale(exchangeResult?.exchange_sale_id || previousExchange!); } catch (cause) { setError(returnProblem(cause)); } }}>Ver venta de cambio y registrar diferencia</button>}</div>}
      {Number(data.available_amount) <= 0 ? <p className="font-semibold">El valor de esta devolución ya está completamente aplicado.</p> : <form onSubmit={submit}>
        <fieldset disabled={busy || loading || !data.can_settle} className="space-y-4">
          <div className="flex flex-wrap gap-2" role="group" aria-label="Destino del valor disponible">{Object.entries(actionLabels).map(([key, label]) => <button type="button" key={key} aria-pressed={action === key} disabled={key === "store-credit" && !data.can_grant_store_credit || key === "settle-debt" && Number(data.debt_to_offset) <= 0 || key === "exchange" && Boolean(previousExchange)} onClick={() => { setAction(key as keyof typeof actionLabels); setAmount(data.available_amount); setError(""); }}>{label}</button>)}</div>
          {action !== "exchange" && <label className="grid gap-2">Justificación de la liquidación<input required minLength={5} maxLength={255} value={reason} onChange={event => setReason(event.target.value)} /></label>}
          {action === "refund" && <>
            <p className="text-sm text-slate-500">Registra el desembolso realizado al cliente por el mismo medio de su pago. El registro no ejecuta transferencias bancarias ni devoluciones en el proveedor de tarjeta.</p>
            <label className="grid gap-2">Pago original<select required value={paymentId} onChange={event => { setPaymentId(event.target.value); setError(""); }}><option value="">Seleccionar pago</option>{payments.map(item => <option key={item.id} value={item.id}>{item.payment_method === "CASH" ? "Efectivo" : item.payment_method} · {item.currency || sale.currency} {item.amount} · {item.reference_code || item.id.slice(0, 8)}</option>)}</select></label>
            {!payments.length && <p>No hay pagos monetarios de origen en esta venta. El valor puede aplicarse a la deuda o como saldo a favor.</p>}
            {optionsLoading && <p role="status">Verificando saldo del pago y cajas autorizadas…</p>}
            {options && <p>Máximo reembolsable en este pago: <strong>{money(cap)}</strong></p>}
            {options?.payment_method === "CASH" && <label className="grid gap-2">Caja autorizada para el retiro<select required value={cashSessionId} onChange={event => setCashSessionId(event.target.value)}><option value="">Seleccionar caja abierta</option>{options.cash_sessions.map(item => <option key={item.id} value={item.id}>{item.terminal_code} · Disponible {money(item.balance)}</option>)}</select>{!options.cash_sessions.length && <span className="text-sm text-amber-600">No hay una caja abierta y autorizada en la sede y moneda de este pago.</span>}</label>}
            <label className="grid gap-2">Referencia del desembolso<input required minLength={3} maxLength={128} value={reference} onChange={event => setReference(event.target.value)} placeholder="Referencia bancaria, del proveedor o acta de efectivo" /></label>
          </>}
          {(action === "refund" || action === "store-credit") && <label className="grid gap-2">Importe ({data.currency})<input type="number" required min="0.000001" step="0.000001" max={action === "refund" ? cap : data.available_amount} value={amount} onChange={event => setAmount(event.target.value)} /></label>}
          {action === "settle-debt" && <p>Se compensará hasta {money(data.debt_to_offset)} de la deuda de la venta original.</p>}
          {action === "exchange" && <>
            <p className="text-sm text-slate-500">El cambio directo crea una venta en la moneda base y en la sede original. Para artículos con series, lotes o kits, otorga saldo a favor y úsalo desde una nueva venta POS.</p>
            <label className="grid gap-2">Buscar producto de reemplazo<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Nombre o SKU" /></label>
            {productsLoading && <p role="status">Consultando productos…</p>}
            <div className="max-h-52 space-y-2 overflow-y-auto">{products.map(product => <div className="flex items-center justify-between gap-3 rounded-xl border p-3" key={product.id}><div><strong>{product.name}</strong><p className="text-xs">{product.sku} · Precio base {product.unit_price} · Disponible {product.available_quantity}</p>{(product.has_serials || product.has_lots) && <p className="text-xs">Requiere el flujo de venta POS.</p>}</div><button type="button" disabled={product.has_serials || product.has_lots || product.track_inventory && Number(product.available_quantity) <= 0} onClick={() => setCart(previous => previous.some(item => item.product.id === product.id) ? previous : [...previous, { product, quantity: 1 }])}>Agregar</button></div>)}{!productsLoading && !products.length && <p>No se encontraron productos.</p>}</div>
            {cart.map(item => <div key={item.product.id} className="flex flex-wrap items-center gap-3"><strong>{item.product.name}</strong><label>Cantidad <input aria-label={`Cantidad de ${item.product.name}`} type="number" min="0.000001" step="0.000001" required max={item.product.track_inventory ? item.product.available_quantity : undefined} value={item.quantity} onChange={event => setCart(previous => previous.map(row => row.product.id === item.product.id ? { ...row, quantity: Number(event.target.value) } : row))} /></label><button type="button" onClick={() => setCart(previous => previous.filter(row => row.product.id !== item.product.id))}>Quitar</button></div>)}
            <p className="font-semibold">Total estimado con impuestos: {money(cart.reduce((sum, item) => sum + item.quantity * Number(item.product.unit_price) * (1 + Number(item.product.tax_rate)), 0))}</p>
          </>}
          <button type="submit" className="sales-return-primary" disabled={action === "refund" && (optionsLoading || !options || cap <= 0 || Boolean(options.payment_method === "CASH" && !cashSessionId)) || action === "exchange" && !cart.length}>{busy ? "Registrando…" : action === "refund" ? "Registrar desembolso" : action === "exchange" ? "Confirmar cambio de producto" : "Registrar aplicación"}</button>
        </fieldset>
      </form>}
    </>}
  </section>;
}
