import type { useCompanySelectorModal } from "../../hooks/useCompanySelectorModal";
import { Building2, Search, Check, AlertCircle, LoaderCircle, ShieldAlert } from "lucide-react";
import { formatRoleLabel } from "../../../../ui/components/AppNavbar";
import { CompanySelectorModalProps } from "../../types/CompanySelectorModal";

export function Panel1({ searchInputRef, search, setSearch, loading, error, loadCompanies, filtered, currentCompanyId, switching, handleSelect }: { searchInputRef: ReturnType<typeof useCompanySelectorModal>["searchInputRef"]; search: ReturnType<typeof useCompanySelectorModal>["search"]; setSearch: ReturnType<typeof useCompanySelectorModal>["setSearch"]; loading: ReturnType<typeof useCompanySelectorModal>["loading"]; error: ReturnType<typeof useCompanySelectorModal>["error"]; loadCompanies: ReturnType<typeof useCompanySelectorModal>["loadCompanies"]; filtered: ReturnType<typeof useCompanySelectorModal>["filtered"]; switching: ReturnType<typeof useCompanySelectorModal>["switching"]; handleSelect: ReturnType<typeof useCompanySelectorModal>["handleSelect"] } & { currentCompanyId: CompanySelectorModalProps["currentCompanyId"] }) {
  return (<div className="p-6 space-y-4">
    <div className="relative">
      <Search className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
      <input
        ref={searchInputRef}
        type="search"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Buscar empresa por nombre o RUC/NIT..."
        aria-label="Buscar empresas disponibles"
        className="w-full rounded-xl border border-slate-200 dark:border-slate-700/80 bg-slate-50/70 dark:bg-slate-950/60 py-2.5 pl-10 pr-4 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none transition focus:border-teal-500 dark:focus:border-teal-400 focus:ring-4 focus:ring-teal-500/15 dark:focus:ring-teal-400/20"
      />
    </div>

    {loading && (
      <div role="status" className="flex items-center justify-center gap-2.5 py-10 text-sm text-slate-500 dark:text-slate-400">
        <LoaderCircle className="h-5 w-5 motion-safe:animate-spin text-teal-600 dark:text-teal-400" />
        <span>Cargando empresas asociadas...</span>
      </div>
    )}

    {error && (
      <div role="alert" className="flex items-start gap-3 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 p-4 text-sm text-red-800 dark:text-red-300">
        <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
        <div className="flex-1">
          <p className="font-medium text-red-900 dark:text-red-200">Error de conexión</p>
          <p className="mt-1 text-xs text-red-700 dark:text-red-400">{error}</p>
          <button
            type="button"
            onClick={loadCompanies}
            className="mt-2 text-xs font-semibold text-red-700 dark:text-red-400 underline hover:no-underline"
          >
            Reintentar
          </button>
        </div>
      </div>
    )}

    {!loading && !error && filtered.length === 0 && (
      <div role="status" className="py-12 text-center text-sm text-slate-500 dark:text-slate-400">
        <Building2 className="mx-auto mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
        <p className="font-medium text-slate-700 dark:text-slate-300">Sin empresas encontradas</p>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
          {search ? "No hay resultados para la búsqueda ingresada." : "Esta cuenta no tiene empresas asociadas activas."}
        </p>
      </div>
    )}

    {!loading && filtered.length > 0 && (
      <ul role="list" className="space-y-2.5 max-h-72 overflow-y-auto">
        {filtered.map(comp => {
          const isCurrent = comp.company_id === currentCompanyId || comp.is_current;
          const isBusy = switching === comp.company_id;
          return (
            <li key={comp.company_id}>
              <button
                type="button"
                disabled={!comp.is_active || isBusy}
                onClick={() => handleSelect(comp)}
                className={`w-full flex items-center justify-between p-4 rounded-2xl border text-left transition ${isCurrent
                  ? "border-teal-500/80 bg-teal-50/70 dark:border-teal-500/70 dark:bg-teal-950/40 ring-1 ring-teal-500/30 dark:ring-teal-400/30"
                  : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/40 hover:border-teal-400 dark:hover:border-teal-500/60 hover:bg-slate-50/80 dark:hover:bg-slate-800/80"
                  } ${!comp.is_active ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="min-w-0 pr-3">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900 dark:text-white truncate">
                      {comp.legal_name}
                    </span>
                    {isCurrent && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-teal-600 dark:bg-teal-500 px-2.5 py-0.5 text-[10px] font-bold text-white shadow-xs">
                        <Check className="h-3 w-3 stroke-[2.5]" /> Activa
                      </span>
                    )}
                    {!comp.is_active && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-950/60 border border-red-200 dark:border-red-800 px-2.5 py-0.5 text-[10px] font-medium text-red-700 dark:text-red-300">
                        <ShieldAlert className="h-3 w-3" /> Inactiva
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    RUC: <span className="font-mono text-slate-700 dark:text-slate-300">{comp.tax_id}</span> · Rol: <span className="font-medium text-slate-700 dark:text-slate-200">{formatRoleLabel(comp.role)}</span>
                  </p>
                </div>
                {isBusy && <LoaderCircle className="h-5 w-5 motion-safe:animate-spin text-teal-600 dark:text-teal-400" />}
              </button>
            </li>
          );
        })}
      </ul>
    )}
  </div>);
}
