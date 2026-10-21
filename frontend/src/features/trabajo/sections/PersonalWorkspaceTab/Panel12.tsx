import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { X } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";

export function Panel12({ setSelectedOrderModal, selectedOrderModal, baseCurrency, onNavigate }: { setSelectedOrderModal: ReturnType<typeof usePersonalWorkspaceTab>["setSelectedOrderModal"]; selectedOrderModal: NonNullable<ReturnType<typeof usePersonalWorkspaceTab>["selectedOrderModal"]> } & { baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]>; onNavigate: PersonalWorkspaceTabProps["onNavigate"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" onMouseDown={e => { if (e.target === e.currentTarget) setSelectedOrderModal(null); }}>
    <div className="w-full max-w-md rounded-3xl bg-white dark:bg-slate-900 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <div>
          <span className="text-[11px] font-semibold text-teal-700 dark:text-teal-400">Detalle de Pedido</span>
          <h3 className="font-bold text-slate-900 dark:text-slate-100">{selectedOrderModal.order_number}</h3>
        </div>
        <button
          type="button"
          onClick={() => setSelectedOrderModal(null)}
          className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Cliente:</span>
          <span className="font-semibold text-slate-900 dark:text-slate-100">{selectedOrderModal.customer_name || selectedOrderModal.customer_id}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Monto total:</span>
          <span className="font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {formatMoney(selectedOrderModal.total_amount, selectedOrderModal.currency || baseCurrency)}
          </span>
        </div>
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Estado:</span>
          <span className="font-semibold text-slate-900 dark:text-slate-100">{selectedOrderModal.status}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Fecha de emisión:</span>
          <span className="text-slate-700 dark:text-slate-300">{new Date(selectedOrderModal.created_at).toLocaleString("es-PE")}</span>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
        <button
          type="button"
          onClick={() => setSelectedOrderModal(null)}
          className="rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          Cerrar
        </button>
        {onNavigate && (
          <button
            type="button"
            onClick={() => {
              setSelectedOrderModal(null);
              onNavigate("orders");
            }}
            className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800"
          >
            Abrir en Pedidos
          </button>
        )}
      </div>
    </div>
  </div>);
}
