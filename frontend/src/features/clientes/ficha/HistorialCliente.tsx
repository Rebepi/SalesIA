import { useState } from "react";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
import { CompraClienteDetalle, estadoCliente, fechaCliente, importeCliente } from "./CompraClienteDetalle";
import { btnSecondary, inputStyle } from "./estilos";

export function HistorialCliente({ model, onAction, canWrite }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { statement, timeline } = model;
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [saleId, setSaleId] = useState<string | null>(null);
  const [timelineLimit, setTimelineLimit] = useState(10);
  const invoices = statement?.invoices || [];
  const filtered = invoices.filter(item => `${item.series_number} ${estadoCliente(item.status)} ${item.currency || ""}`.toLowerCase().includes(search.toLowerCase()));
  const currencies = [...new Set(invoices.map(item => String(item.currency || "")))];
  const validInvoices = invoices.filter(item => ["confirmed", "paid"].includes(String(item.status)));
  return <div className="space-y-5">
    <div className="customer-purchase-section">
      <h3>Resumen de compras</h3>
      <p className="mb-4 text-xs text-slate-400">{invoices.length} operaciones registradas. Los importes incluyen ventas confirmadas y pagadas, separados por moneda; los borradores y anulaciones se conservan en el historial.</p>
      {currencies.map(currency => {
        const group = validInvoices.filter(item => String(item.currency || "") === currency);
        const sum = (field: string) => group.some(item => item[field] == null) ? null : group.reduce((total, item) => total + Number(item[field]), 0);
        return <div key={currency} className="mb-3 grid gap-3 sm:grid-cols-3">{[["Total comprado", sum("total_amount")], ["Total cobrado", sum("paid_amount")], ["Pendiente en ventas", sum("pending_balance")]].map(([label, value]) => <div className="customer-purchase-metric" key={String(label)}><span>{label}</span><strong>{importeCliente(value, currency)}</strong></div>)}</div>;
      })}
      {!invoices.length && <p>No hay compras registradas para este cliente.</p>}
    </div>
    <section className="customer-purchase-section" aria-label="Compras del cliente">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h3>Compras y comprobantes</h3><input className={`${inputStyle} sm:max-w-xs`} aria-label="Buscar compra" placeholder="Documento, estado o moneda" value={search} onChange={event => { setSearch(event.target.value); setPage(0); }} /></div>
      <div className="overflow-x-auto"><table><thead><tr><th>Documento / fecha</th><th>Estado / condición</th><th className="amount">Total</th><th className="amount">Cobrado</th><th className="amount">Pendiente</th><th>Acciones</th></tr></thead><tbody>
        {filtered.slice(page * 10, page * 10 + 10).map((invoice, index) => <tr key={String(invoice.sale_id || index)}>
          <td><strong>{String(invoice.series_number || "Sin numerar")}</strong><p className="text-xs text-slate-400">{fechaCliente(invoice.created_at)}</p></td>
          <td>{estadoCliente(invoice.status)}<p className="text-xs text-slate-400">{invoice.is_credit ? "Crédito" : "Contado"}</p></td>
          <td className="amount">{importeCliente(invoice.total_amount, String(invoice.currency || ""))}</td><td className="amount">{importeCliente(invoice.paid_amount, String(invoice.currency || ""))}</td><td className="amount">{["draft", "cancelled"].includes(String(invoice.status)) ? "No aplica" : importeCliente(invoice.pending_balance, String(invoice.currency || ""))}</td>
          <td><div className="flex flex-wrap gap-2"><button type="button" className={btnSecondary} onClick={() => setSaleId(String(invoice.sale_id))} aria-expanded={saleId === String(invoice.sale_id)}>Ver compra</button>{canWrite && onAction && <button type="button" className={btnSecondary} onClick={() => onAction("repeat", String(invoice.sale_id))}>Repetir venta</button>}</div></td>
        </tr>)}
        {!filtered.length && <tr><td colSpan={6}>No hay operaciones que coincidan.</td></tr>}
      </tbody></table></div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs"><span>{filtered.length} operaciones · Página {page + 1} de {Math.max(1, Math.ceil(filtered.length / 10))}</span><div className="flex gap-2"><button type="button" className={btnSecondary} disabled={page === 0} onClick={() => setPage(value => value - 1)}>Anterior</button><button type="button" className={btnSecondary} disabled={(page + 1) * 10 >= filtered.length} onClick={() => setPage(value => value + 1)}>Siguiente</button></div></div>
    </section>
    {saleId && <CompraClienteDetalle saleId={saleId} onClose={() => setSaleId(null)} />}
    <section className="customer-purchase-section"><h3>Actividad comercial ({timeline.length})</h3>{timeline.slice(0, timelineLimit).map((event, index) => <div key={String(event.id || index)} className="mb-2 flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200 p-3 text-xs"><div><strong className="capitalize">{estadoCliente(event.type)}</strong><p>{String(event.reference || event.subject || event.content || "Actividad")}</p></div><div className="text-right"><span className="block text-slate-400">{fechaCliente(event.date)}</span>{event.amount != null && <span>{importeCliente(event.amount, String(event.currency || ""))}</span>}</div></div>)}{!timeline.length && <p>Sin actividades comerciales registradas.</p>}{timeline.length > timelineLimit && <button type="button" className={btnSecondary} onClick={() => setTimelineLimit(value => value + 10)}>Mostrar más actividad</button>}</section>
  </div>;
}
