import type { useOrdersWorkspaceTab } from "../../hooks/useOrdersWorkspaceTab";
import { X, History } from "lucide-react";
import { OrderBillingPanel } from "../../components/OrderBillingPanel";

export function SeccionCantidadesPedidasVsServidas({ selectedOrder, setSelectedOrder, canWrite, editOrderLines }: { selectedOrder: NonNullable<ReturnType<typeof useOrdersWorkspaceTab>["selectedOrder"]>; setSelectedOrder: ReturnType<typeof useOrdersWorkspaceTab>["setSelectedOrder"]; editOrderLines: ReturnType<typeof useOrdersWorkspaceTab>["editOrderLines"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-xs p-4">
    <div role="dialog" aria-labelledby="ord-detail-title" className="app-modal-panel w-full max-w-xl rounded-3xl bg-white shadow-2xl overflow-hidden animate-in zoom-in-95">
      <header className="flex items-center justify-between border-b border-slate-100 p-6 bg-slate-50">
        <div>
          <h3 id="ord-detail-title" className="text-base font-bold text-slate-900">
            Cantidades Pedidas vs Servidas: {selectedOrder.order_number}
          </h3>
          <p className="text-xs text-slate-500">Trazabilidad de unidades solicitadas, reservadas y despachadas</p>
        </div>
        <button type="button" onClick={() => setSelectedOrder(null)} className="text-slate-400 hover:text-slate-700">
          <X className="h-5 w-5" />
        </button>
      </header>
      <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto text-xs">
        <table className="w-full text-left">
          <thead className="border-b border-slate-200 text-slate-500 font-semibold">
            <tr>
              <th className="pb-2">Producto</th>
              <th className="pb-2 text-right">Pedida</th>
              <th className="pb-2 text-right">Reservada</th>
              <th className="pb-2 text-right">Servida</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {selectedOrder.lines?.map((l, i) => (
              <tr key={i}>
                <td className="py-2.5">
                  <strong className="text-slate-900">{l.sku}</strong>
                  <p className="text-[10px] text-slate-400">{l.product_name}</p>
                </td>
                <td className="py-2.5 text-right font-mono font-bold">{l.quantity}</td>
                <td className="py-2.5 text-right font-mono text-teal-700">{l.reserved_quantity || "0"}</td>
                <td className="py-2.5 text-right font-mono text-emerald-700">{l.fulfilled_quantity || "0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <section className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700"><h4 className="mb-3 flex items-center gap-2 font-bold text-slate-900 dark:text-white"><History className="h-4 w-4 text-teal-600" />Historial del pedido</h4><div className="space-y-2">{selectedOrder.history?.length ? selectedOrder.history.map((item, index) => <div key={`${item.timestamp}-${index}`} className="flex items-start justify-between gap-4 rounded-xl bg-slate-50 p-3 dark:bg-slate-800"><span><strong className="block text-slate-800 dark:text-slate-100">{item.status}</strong><span className="text-[10px] text-slate-500">{item.note || "Cambio registrado"} · {item.actor || "Sistema"}</span></span><time className="whitespace-nowrap text-[10px] text-slate-500">{new Date(item.timestamp).toLocaleString("es-PE")}</time></div>) : <p className="text-slate-400">Sin eventos adicionales.</p>}</div></section>
        {selectedOrder.id || selectedOrder.order_id ? <OrderBillingPanel orderId={(selectedOrder.id || selectedOrder.order_id)!} canWrite={canWrite && ["confirmed", "partially_fulfilled", "fulfilled", "backorder"].includes(selectedOrder.status)} /> : null}
      </div>
      <footer className="flex justify-end p-4 border-t border-slate-100 bg-slate-50">
        {canWrite && selectedOrder.status === "draft" && <button type="button" onClick={() => { editOrderLines(selectedOrder); setSelectedOrder(null); }} className="mr-2 rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white">Editar líneas</button>}
        <button type="button" onClick={() => setSelectedOrder(null)} className="rounded-xl border border-slate-200 px-4 py-2 font-semibold text-slate-700">
          Cerrar
        </button>
      </footer>
    </div>
  </div>);
}
