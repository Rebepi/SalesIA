import { Panel1 } from "../sections/CompanySelectorModal/Panel1";
export type { CompanyMembership } from "../types/CompanySelectorModal";
import { useCompanySelectorModal } from "../hooks/useCompanySelectorModal";
import { Building2, X } from "lucide-react";
import { CompanySelectorModalProps } from "../types/CompanySelectorModal";

export function CompanySelectorModal({
  isOpen,
  currentCompanyId,
  onClose,
  onCompanySelected
}: CompanySelectorModalProps) {
  const { search, setSearch, loading, error, switching, dialogRef, searchInputRef, loadCompanies, handleSelect, filtered } = useCompanySelectorModal({ isOpen, currentCompanyId, onClose, onCompanySelected });
  if (!isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      id="scr-002-company-selector-dialog"
      role="dialog"
      onCancel={onClose}
      aria-labelledby="scr-002-title"
      className="max-h-[90vh] w-[min(94vw,560px)] rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-0 shadow-2xl text-slate-900 dark:text-slate-100 backdrop:bg-slate-950/70"
    >
      <header className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 p-6 bg-slate-50/50 dark:bg-slate-900/50">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-teal-500/10 dark:bg-teal-400/10 text-teal-600 dark:text-teal-400">
              <Building2 className="h-4.5 w-4.5" />
            </div>
            <h2 id="scr-002-title" className="text-lg font-semibold text-slate-900 dark:text-white">
              Seleccionar Empresa / Entorno
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Elige la empresa y ámbito operativo autorizado
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar selector de empresa"
          className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <Panel1 searchInputRef={searchInputRef} search={search} setSearch={setSearch} loading={loading} error={error} loadCompanies={loadCompanies} filtered={filtered} currentCompanyId={currentCompanyId} switching={switching} handleSelect={handleSelect} />

      <footer className="flex justify-end border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/50 p-4">
        <button
          type="button"
          onClick={onClose}
          className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition active:scale-95"
        >
          Cerrar
        </button>
      </footer>
    </dialog>
  );
}
