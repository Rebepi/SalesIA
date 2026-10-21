import { useEffect, useState } from "react";
import { solicitarLoadFullSale } from "../../ventas/api/SaleDetailModal";
import type { SaleDetailData } from "../../ventas/types/SaleDetailModal";
import { btnSecondary } from "./estilos";

export function importeCliente(value: unknown, currency?: string) {
  if (value === null || value === undefined || value === "") return "Restringido";
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "—";
  return `${currency || "Moneda sin registrar"} ${amount.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function fechaCliente(value: unknown) {
  if (!value) return "Sin registrar";
  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? "Sin registrar" : date.toLocaleString("es-PE", { timeZone: "America/Lima", dateStyle: "medium", timeStyle: "short" });
}

export function estadoCliente(value: unknown) {
  const states: Record<string, string> = { draft: "Borrador", confirmed: "Confirmada", paid: "Pagada", cancelled: "Anulada", pending: "Pendiente", refunded: "Reembolsada", sale: "Venta", quotation: "Cotización", order: "Pedido", payment: "Pago", return: "Devolución", activity: "Actividad", note: "Nota", audit: "Auditoría", contact: "Contacto", address: "Dirección", opportunity: "Oportunidad", cash: "Efectivo", card: "Tarjeta", transfer: "Transferencia" };
  return states[String(value)] || String(value || "Sin registrar");
}

export function CompraClienteDetalle({ saleId, onClose }: { saleId: string; onClose: () => void }) {
  const [sale, setSale] = useState<SaleDetailData | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setSale(null);
    setError("");
    solicitarLoadFullSale({ id: saleId, signal: controller.signal }).then(data => {
      if (!controller.signal.aborted) setSale(data);
    }).catch(() => {
      if (!controller.signal.aborted) setError("No se pudo consultar la compra. Comprueba tu acceso a Ventas e inténtalo de nuevo.");
    });
    return () => controller.abort();
  }, [saleId, attempt]);
  return <section className="customer-purchase-section" aria-label="Detalle de la compra" aria-live="polite">
    <div className="mb-4 flex items-center justify-between gap-3"><h3>Detalle de la compra</h3><button type="button" className={btnSecondary} onClick={onClose}>Cerrar detalle</button></div>
    {error ? <div role="alert">{error}<button type="button" className={btnSecondary} onClick={() => setAttempt(value => value + 1)}>Reintentar</button></div> : !sale ? <p role="status">Cargando productos y pagos…</p> : <>
      <dl className="customer-purchase-meta">
        <div><dt>Comprobante</dt><dd>{sale.number || (sale.series ? `${sale.series}-${sale.correlative || ""}` : "Sin numerar")}</dd></div>
        <div><dt>Estado</dt><dd>{estadoCliente(sale.status)}</dd></div>
        <div><dt>Fecha de registro</dt><dd>{fechaCliente(sale.created_at)}</dd></div>
        <div><dt>Condición de pago</dt><dd>{sale.is_credit ? "Crédito" : "Contado"}</dd></div>
        <div><dt>Sede</dt><dd>{sale.branch_name || "Sin registrar"}</dd></div>
        <div><dt>Vendedor</dt><dd>{sale.sales_rep_name || "Sin asignar"}</dd></div>
        <div><dt>Vencimiento</dt><dd>{fechaCliente(sale.due_at || sale.due_date)}</dd></div>
        <div><dt>Entrega</dt><dd>{sale.delivery_status || "Sin registrar"}</dd></div>
      </dl>
      <div className="mb-5 grid gap-3 sm:grid-cols-3">{[["Total", sale.total_amount], ["Cobrado", sale.paid_amount], ["Pendiente", sale.balance_amount ?? (sale.total_amount != null && sale.paid_amount != null ? Number(sale.total_amount) - Number(sale.paid_amount) : null)]].map(([label, value]) => <div className="customer-purchase-metric" key={String(label)}><span>{label}</span><strong>{importeCliente(value, sale.currency)}</strong></div>)}</div>
      <h3>Productos comprados ({sale.lines?.length || 0})</h3>
      <div className="overflow-x-auto"><table><thead><tr><th>Producto / SKU</th><th className="amount">Cantidad</th><th className="amount">Precio unitario</th><th className="amount">Descuento</th><th className="amount">Impuesto</th><th className="amount">Total de línea</th></tr></thead><tbody>{sale.lines?.map((line, index) => <tr key={line.id || index}><td><strong>{line.product_name || line.name}</strong><p className="text-slate-400">{line.sku || "Sin SKU"}</p></td><td className="amount">{Number(line.quantity).toLocaleString("es-PE")} {line.unit_of_measure}</td><td className="amount">{importeCliente(line.unit_price, sale.currency)}</td><td className="amount">{importeCliente(line.discount, sale.currency)}</td><td className="amount">{importeCliente(line.tax_amount, sale.currency)}</td><td className="amount">{importeCliente(line.total_amount, sale.currency)}</td></tr>)}{!sale.lines?.length && <tr><td colSpan={6}>No hay productos registrados en esta operación.</td></tr>}</tbody></table></div>
      <h3 className="mt-5">Pagos registrados</h3>
      <div className="overflow-x-auto"><table><thead><tr><th>Fecha</th><th>Medio</th><th>Referencia</th><th className="amount">Importe</th></tr></thead><tbody>{sale.payments?.map(payment => <tr key={payment.id}><td>{fechaCliente(payment.created_at)}</td><td>{estadoCliente(payment.payment_method)}{payment.is_reversal ? " · Reversado" : ""}</td><td>{payment.reference_code || "Sin referencia"}</td><td className="amount">{importeCliente(payment.amount, payment.currency || sale.currency)}</td></tr>)}{!sale.payments?.length && <tr><td colSpan={4}>No hay pagos registrados.</td></tr>}</tbody></table></div>
      {!!sale.installments?.length && <><h3 className="mt-5">Cuotas</h3><div className="overflow-x-auto"><table><thead><tr><th>Cuota</th><th>Vencimiento</th><th>Estado</th><th className="amount">Importe</th><th className="amount">Pagado</th></tr></thead><tbody>{sale.installments.map((item, index) => <tr key={index}><td>{item.number}</td><td>{fechaCliente(item.due_date)}</td><td>{estadoCliente(item.status)}</td><td className="amount">{importeCliente(item.amount, sale.currency)}</td><td className="amount">{importeCliente(item.paid_amount, sale.currency)}</td></tr>)}</tbody></table></div></>}
      {!!sale.returns?.length && <><h3 className="mt-5">Devoluciones</h3>{sale.returns.map(item => <div className="customer-purchase-metric mb-2" key={item.id}><strong>{item.return_number} · {importeCliente(item.total_refunded, sale.currency)}</strong><p>{item.reason}</p><p className="text-slate-400">{fechaCliente(item.date)} · {item.money_destination}</p>{item.items?.map((product, index) => <p key={index}>{product.product_name} · {product.quantity} unidades · {importeCliente(product.amount, sale.currency)}</p>)}</div>)}</>}
      {sale.notes && <div className="mt-5"><h3>Observaciones de la venta</h3><p className="whitespace-pre-wrap">{sale.notes}</p></div>}
    </>}
  </section>;
}
