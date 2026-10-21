import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { X } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";

export function Panel13({ setSelectedCustomerModal, selectedCustomerModal, baseCurrency, onNavigate }: { setSelectedCustomerModal: ReturnType<typeof usePersonalWorkspaceTab>["setSelectedCustomerModal"]; selectedCustomerModal: NonNullable<ReturnType<typeof usePersonalWorkspaceTab>["selectedCustomerModal"]> } & { baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]>; onNavigate: PersonalWorkspaceTabProps["onNavigate"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" onMouseDown={e => { if (e.target === e.currentTarget) setSelectedCustomerModal(null); }}>
    <div className="w-full max-w-md rounded-3xl bg-white dark:bg-slate-900 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <div>
          <span className="text-[11px] font-semibold text-teal-700 dark:text-teal-400">Ficha de Cliente</span>
          <h3 className="font-bold text-slate-900 dark:text-slate-100">{selectedCustomerModal.legal_name}</h3>
        </div>
        <button
          type="button"
          onClick={() => setSelectedCustomerModal(null)}
          className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Documento / RUC:</span>
          <span className="font-mono font-semibold text-slate-900 dark:text-slate-100">{selectedCustomerModal.doc_number || "—"}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Código interno:</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">{selectedCustomerModal.code || "—"}</span>
        </div>
        <div className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800">
          <span className="text-slate-500 dark:text-slate-400">Saldo pendiente:</span>
          <span className="font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {selectedCustomerModal.current_balance !== null && selectedCustomerModal.current_balance !== undefined
              ? formatMoney(selectedCustomerModal.current_balance, baseCurrency)
              : "Saldo restringido por seguridad"}
          </span>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
        <button
          type="button"
          onClick={() => setSelectedCustomerModal(null)}
          className="rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          Cerrar
        </button>
        {onNavigate && (
          <button
            type="button"
            onClick={() => {
              setSelectedCustomerModal(null);
              onNavigate("customers");
            }}
            className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800"
          >
            Abrir en Clientes
          </button>
        )}
      </div>
    </div>
  </div>);
}
