import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X, Search, ChevronDown } from "lucide-react";

export function Panel3({ showFilters, setShowFilters, setCategoryDropdownOpen, filterButtonRef, period, setPeriod, branchId, setBranchId, branches, currency, setCurrency, summaryData, categoryContainerRef, categoryDropdownOpen, category, categorySearch, setCategorySearch, setCategory, filteredCategories, hasActiveFilters, activeBranchObj, periodLabel, handleResetFilters }: { showFilters: ReturnType<typeof useDashboardAnalyticsTab>["showFilters"]; setShowFilters: ReturnType<typeof useDashboardAnalyticsTab>["setShowFilters"]; setCategoryDropdownOpen: ReturnType<typeof useDashboardAnalyticsTab>["setCategoryDropdownOpen"]; filterButtonRef: ReturnType<typeof useDashboardAnalyticsTab>["filterButtonRef"]; period: ReturnType<typeof useDashboardAnalyticsTab>["period"]; setPeriod: ReturnType<typeof useDashboardAnalyticsTab>["setPeriod"]; branchId: ReturnType<typeof useDashboardAnalyticsTab>["branchId"]; setBranchId: ReturnType<typeof useDashboardAnalyticsTab>["setBranchId"]; branches: ReturnType<typeof useDashboardAnalyticsTab>["branches"]; currency: ReturnType<typeof useDashboardAnalyticsTab>["currency"]; setCurrency: ReturnType<typeof useDashboardAnalyticsTab>["setCurrency"]; summaryData: ReturnType<typeof useDashboardAnalyticsTab>["summaryData"]; categoryContainerRef: ReturnType<typeof useDashboardAnalyticsTab>["categoryContainerRef"]; categoryDropdownOpen: ReturnType<typeof useDashboardAnalyticsTab>["categoryDropdownOpen"]; category: ReturnType<typeof useDashboardAnalyticsTab>["category"]; categorySearch: ReturnType<typeof useDashboardAnalyticsTab>["categorySearch"]; setCategorySearch: ReturnType<typeof useDashboardAnalyticsTab>["setCategorySearch"]; setCategory: ReturnType<typeof useDashboardAnalyticsTab>["setCategory"]; filteredCategories: ReturnType<typeof useDashboardAnalyticsTab>["filteredCategories"]; hasActiveFilters: ReturnType<typeof useDashboardAnalyticsTab>["hasActiveFilters"]; activeBranchObj: ReturnType<typeof useDashboardAnalyticsTab>["activeBranchObj"]; periodLabel: ReturnType<typeof useDashboardAnalyticsTab>["periodLabel"]; handleResetFilters: ReturnType<typeof useDashboardAnalyticsTab>["handleResetFilters"] }) {
  return (<div className="dashboard-filter-area">
    <div>
      <div
        id="dashboard-filter-panel"
        role="region"
        aria-label="Filtros del resumen ejecutivo"
        hidden={!showFilters}
        onKeyDown={event => {
          if (event.key === "Escape") {
            event.stopPropagation();
            setShowFilters(false);
            setCategoryDropdownOpen(false);
            filterButtonRef.current?.focus();
          }
        }}
        className="dashboard-filter-panel rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <div className="col-span-full flex items-start justify-between gap-3">
          <div><p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Filtrar resultados</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Los cambios se aplican automáticamente a todos los paneles.</p></div>
          <button type="button" aria-label="Cerrar filtros" onClick={() => { setShowFilters(false); setCategoryDropdownOpen(false); filterButtonRef.current?.focus(); }} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"><X className="h-4 w-4" /></button>
        </div>

        <div className="dashboard-filter-field"><label htmlFor="dash-period-select" className="mb-2 block text-xs font-medium text-slate-600 dark:text-slate-400">Periodo</label>
          <CustomSelect
            id="dash-period-select"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            aria-label="Periodo de tiempo"
            className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm outline-none transition focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
            <option value="90d">Últimos 90 días</option>
            <option value="12m">Últimos 12 meses</option>
            <option value="all">Todo el historial</option>
          </CustomSelect>
        </div>

        <div className="dashboard-filter-field"><label htmlFor="dash-branch-select" className="mb-2 block text-xs font-medium text-slate-600 dark:text-slate-400">Sede</label>
          <CustomSelect remote={{ resource: "branches" }}
            id="dash-branch-select"
            value={branchId}
            onChange={(e) => setBranchId(e.target.value)}
            aria-label="Sede comercial"
            className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm outline-none transition focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="">Todas las sedes</option>
            {branches.map((b) => (
              <option key={b.branch_id} value={b.branch_id}>
                {b.name} ({b.code})
              </option>
            ))}
          </CustomSelect>
        </div>

        <div className="dashboard-filter-field"><label htmlFor="dash-currency-select" className="mb-2 block text-xs font-medium text-slate-600 dark:text-slate-400">Moneda</label>
          <CustomSelect
            id="dash-currency-select"
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            aria-label="Moneda de transacción"
            title="Solo filtra ventas emitidas en la moneda seleccionada (sin conversión cambiaria)"
            className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm outline-none transition focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="">Moneda base ({summaryData?.currency || "USD"})</option>
            <option value="USD">USD</option>
            <option value="PEN">PEN</option>
            <option value="EUR">EUR</option>
          </CustomSelect>
        </div>

        <div className="dashboard-filter-field relative" ref={categoryContainerRef}>
          <span className="mb-2 block text-xs font-medium text-slate-600 dark:text-slate-400">Categoría</span>
          <button
            type="button"
            aria-label="Categoría de producto"
            onClick={() => setCategoryDropdownOpen(!categoryDropdownOpen)}
            className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm outline-none transition focus:border-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            aria-expanded={categoryDropdownOpen}
            aria-haspopup="listbox"
          >
            <span>{category ? `Categoría: ${category}` : "Todas las categorías"}</span>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>

          {categoryDropdownOpen && (
            <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-700 dark:bg-slate-800">
              <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs dark:border-slate-700 dark:bg-slate-900">
                <Search className="h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar categoría..."
                  value={categorySearch}
                  onChange={(e) => setCategorySearch(e.target.value)}
                  className="w-full bg-transparent outline-none text-slate-800 dark:text-slate-200"
                  autoFocus
                />
                {categorySearch && (
                  <button
                    type="button"
                    onClick={() => setCategorySearch("")}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>

              <div className="mt-2 max-h-48 overflow-y-auto space-y-1">
                <button
                  type="button"
                  onClick={() => {
                    setCategory("");
                    setCategoryDropdownOpen(false);
                  }}
                  className={`w-full text-left rounded-lg px-2.5 py-1.5 text-xs transition ${!category
                    ? "bg-teal-50 font-semibold text-teal-800 dark:bg-teal-950/60 dark:text-teal-200"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
                    }`}
                >
                  Todas las categorías
                </button>
                {filteredCategories.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => {
                      setCategory(cat.name);
                      setCategoryDropdownOpen(false);
                    }}
                    className={`w-full text-left rounded-lg px-2.5 py-1.5 text-xs transition ${category === cat.name
                      ? "bg-teal-50 font-semibold text-teal-800 dark:bg-teal-950/60 dark:text-teal-200"
                      : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
                      }`}
                  >
                    {cat.name} <span className="text-[10px] text-slate-400">({cat.code})</span>
                  </button>
                ))}
                {filteredCategories.length === 0 && (
                  <p className="p-2 text-center text-xs text-slate-400">Sin categorías coincidentes</p>
                )}
              </div>
            </div>
          )}
        </div>

        {hasActiveFilters && (
          <div className="dashboard-active-filters col-span-full flex flex-wrap items-center gap-2.5 border-t border-slate-100 pt-4 mt-2 dark:border-slate-800" aria-label="Filtros activos">
            <span className="mr-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Aplicados:</span>
            {branchId && (
              <span className="inline-flex max-w-full items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300">
                Sede: {activeBranchObj?.name || branchId.slice(0, 8)}
                <button
                  type="button"
                  onClick={() => setBranchId("")}
                  aria-label="Quitar filtro de sede"
                  className="shrink-0 rounded p-0.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 focus-visible:outline focus-visible:outline-teal-500 dark:hover:bg-slate-700 dark:hover:text-white"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {category && (
              <span className="inline-flex max-w-full items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300">
                Categoría: {category}
                <button
                  type="button"
                  onClick={() => setCategory("")}
                  aria-label="Quitar filtro de categoría"
                  className="shrink-0 rounded p-0.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 focus-visible:outline focus-visible:outline-teal-500 dark:hover:bg-slate-700 dark:hover:text-white"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}

            {currency && (
              <span className="inline-flex max-w-full items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300">
                Moneda: {currency}
                <button
                  type="button"
                  onClick={() => setCurrency("")}
                  aria-label="Quitar filtro de moneda"
                  className="shrink-0 rounded p-0.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 focus-visible:outline focus-visible:outline-teal-500 dark:hover:bg-slate-700 dark:hover:text-white"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}

            {period && period !== "30d" && (
              <span className="inline-flex max-w-full items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300">
                {periodLabel}
                <button
                  type="button"
                  onClick={() => setPeriod("30d")}
                  aria-label="Restablecer periodo a 30 días"
                  className="shrink-0 rounded p-0.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-700 focus-visible:outline focus-visible:outline-teal-500 dark:hover:bg-slate-700 dark:hover:text-white"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}

            <button
              type="button"
              onClick={handleResetFilters}
              className="ml-auto rounded px-2.5 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:hover:bg-rose-950/40 dark:hover:text-rose-300 transition-colors"
            >
              Limpiar filtros
            </button>
          </div>
        )}
      </div>




    </div>
  </div>);
}
