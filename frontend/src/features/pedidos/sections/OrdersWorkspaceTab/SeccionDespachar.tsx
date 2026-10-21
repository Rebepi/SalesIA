import type { useOrdersWorkspaceTab } from "../../hooks/useOrdersWorkspaceTab";
import { X } from "lucide-react";

export function SeccionDespachar({ fulfillSerials, setFulfillSerials, fulfillModal, setFulfillModal, handleFulfillSubmit, fulfillQuantities, setFulfillQuantities, busy }: { fulfillSerials: Record<string, string>; setFulfillSerials: ReturnType<typeof useOrdersWorkspaceTab>["setFulfillSerials"]; fulfillModal: NonNullable<ReturnType<typeof useOrdersWorkspaceTab>["fulfillModal"]>; setFulfillModal: ReturnType<typeof useOrdersWorkspaceTab>["setFulfillModal"]; handleFulfillSubmit: ReturnType<typeof useOrdersWorkspaceTab>["handleFulfillSubmit"]; fulfillQuantities: ReturnType<typeof useOrdersWorkspaceTab>["fulfillQuantities"]; setFulfillQuantities: ReturnType<typeof useOrdersWorkspaceTab>["setFulfillQuantities"]; busy: ReturnType<typeof useOrdersWorkspaceTab>["busy"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-xs p-4">
    <div role="dialog" aria-labelledby="ord-fulfill-title" className="app-modal-panel w-full max-w-md rounded-3xl bg-white shadow-2xl overflow-hidden animate-in zoom-in-95">
      <header className="flex items-center justify-between border-b border-slate-100 p-6 bg-slate-50">
        <div>
          <h3 id="ord-fulfill-title" className="text-base font-bold text-slate-900">
            Despachar: {fulfillModal.order_number}
          </h3>
          <p className="text-xs text-slate-500">Ingresa las cantidades entregadas en este despacho</p>
        </div>
        <button type="button" onClick={() => setFulfillModal(null)} className="text-slate-400 hover:text-slate-700">
          <X className="h-5 w-5" />
        </button>
      </header>
      <form onSubmit={handleFulfillSubmit} className="p-6 space-y-4 text-xs">
        {fulfillModal.lines?.map((l, i) => (
          <div key={i} className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <span className="font-bold text-slate-900">{l.sku}</span>
              <p className="text-[10px] text-slate-400">Total: {l.quantity} · Servido: {l.fulfilled_quantity || "0"}</p>
            </div>
            <div className="space-y-2"><input
              type="number"
              min="0"
              step="any"
              value={fulfillQuantities[String(i + 1)] || "0"}
              onChange={e => setFulfillQuantities({ ...fulfillQuantities, [String(i + 1)]: e.target.value })}
              className="w-24 rounded-xl border border-slate-300 p-2 text-right font-mono outline-none focus:border-teal-600"
            /><input aria-label={`Series de la línea ${i + 1}`} placeholder="Series separadas por coma" value={fulfillSerials[String(i + 1)] || ""} onChange={event => setFulfillSerials(previous => ({ ...previous, [String(i + 1)]: event.target.value }))} className="block w-44 rounded-lg border p-2" /></div>
          </div>
        ))}
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={() => setFulfillModal(null)} className="rounded-xl border border-slate-200 px-4 py-2 font-semibold text-slate-700">
            Cancelar
          </button>
          <button type="submit" disabled={busy} className="rounded-xl bg-emerald-700 px-5 py-2 font-semibold text-white hover:bg-emerald-800 disabled:opacity-50">
            {busy ? "Despachando..." : "Confirmar Despacho"}
          </button>
        </div>
      </form>
    </div>
  </div>);
}
