import type { useAccountsReceivableTab } from "../../hooks/useAccountsReceivableTab";
import { X } from "lucide-react";

export function SeccionReconciliacionDeSaldo({ activeItem, setActiveItem, loadingReconcile, creditNotes, reconcileNotes, setReconcileNotes, toast }: { activeItem: NonNullable<ReturnType<typeof useAccountsReceivableTab>["activeItem"]>; setActiveItem: ReturnType<typeof useAccountsReceivableTab>["setActiveItem"]; loadingReconcile: ReturnType<typeof useAccountsReceivableTab>["loadingReconcile"]; creditNotes: ReturnType<typeof useAccountsReceivableTab>["creditNotes"]; reconcileNotes: ReturnType<typeof useAccountsReceivableTab>["reconcileNotes"]; setReconcileNotes: ReturnType<typeof useAccountsReceivableTab>["setReconcileNotes"]; toast: ReturnType<typeof useAccountsReceivableTab>["toast"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-bold text-slate-900">
            Reconciliación de Saldo #{activeItem.series_number}
          </h3>
          <p className="text-xs text-slate-500">
            Verificación de aplicaciones de cobros y notas de crédito emitidas.
          </p>
        </div>
        <button
          onClick={() => setActiveItem(null)}
          className="rounded p-1 text-slate-400 hover:bg-slate-100"
          aria-label="Cerrar conciliación"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-4 space-y-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">Monto total facturado:</span>
            <span className="font-semibold text-slate-900">${Number(activeItem.total_amount).toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Cobros registrados:</span>
            <span className="font-semibold text-teal-700">${Number(activeItem.paid_amount).toFixed(2)}</span>
          </div>
          <div className="flex justify-between border-t border-slate-200 pt-1.5 font-bold">
            <span className="text-slate-700">Saldo remanente por cobrar:</span>
            <span className="text-rose-700">${Number(activeItem.balance_due).toFixed(2)}</span>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Notas de Crédito Vinculadas
          </h4>
          {loadingReconcile ? (
            <p className="mt-2 text-xs text-slate-400">Consultando libro fiscal…</p>
          ) : creditNotes.length === 0 ? (
            <p className="mt-2 text-xs text-slate-400">No hay notas de crédito aplicadas a esta venta.</p>
          ) : (
            <div className="mt-2 space-y-1.5">
              {creditNotes.map(cn => (
                <div key={cn.id} className="flex items-center justify-between rounded-lg border border-slate-100 p-2 text-xs">
                  <div>
                    <span className="font-mono font-bold text-slate-800">{cn.series}-{cn.number}</span>
                    <span className="ml-2 text-slate-400">{cn.created_at.slice(0, 10)}</span>
                  </div>
                  <span className="font-semibold text-teal-700">${Number(cn.total_amount).toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-slate-100 pt-3">
          <label className="block text-xs font-semibold text-slate-700">
            Observaciones de Reconciliación
            <textarea
              rows={2}
              value={reconcileNotes}
              onChange={e => setReconcileNotes(e.target.value)}
              placeholder="Detalle de concordancia con extracto bancario o ajuste contable"
              className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs outline-none focus:ring-2 focus:ring-teal-200"
            />
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => setActiveItem(null)}
            className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700"
          >
            Cerrar
          </button>
          <button
            type="button"
            onClick={() => {
              toast.success("Saldo reconciliado", "El balance fue verificado contra cobros y notas de crédito.");
              setActiveItem(null);
            }}
            className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 transition"
            data-testid="confirm-reconciliation-btn"
          >
            Aceptar Reconciliación
          </button>
        </div>
      </div>
    </div>
  </div>);
}
