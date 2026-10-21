import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { RefreshCw, Download, Filter, Layers, ChevronDown, Clock } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function Panel1({ periodLabel, isUpdatingAny, summaryError, minutesSinceUpdate, currency, activeCurrency, filterButtonRef, setShowFilters, setCategoryDropdownOpen, showFilters, activeFilterCount, autoRefreshInterval, setAutoRefreshInterval, handleRefreshAll, setShowConfig, showConfig, exportSummaryCSV, exporting, summaryData }: { periodLabel: ReturnType<typeof useDashboardAnalyticsTab>["periodLabel"]; isUpdatingAny: ReturnType<typeof useDashboardAnalyticsTab>["isUpdatingAny"]; summaryError: ReturnType<typeof useDashboardAnalyticsTab>["summaryError"]; minutesSinceUpdate: ReturnType<typeof useDashboardAnalyticsTab>["minutesSinceUpdate"]; currency: ReturnType<typeof useDashboardAnalyticsTab>["currency"]; activeCurrency: ReturnType<typeof useDashboardAnalyticsTab>["activeCurrency"]; filterButtonRef: ReturnType<typeof useDashboardAnalyticsTab>["filterButtonRef"]; setShowFilters: ReturnType<typeof useDashboardAnalyticsTab>["setShowFilters"]; setCategoryDropdownOpen: ReturnType<typeof useDashboardAnalyticsTab>["setCategoryDropdownOpen"]; showFilters: ReturnType<typeof useDashboardAnalyticsTab>["showFilters"]; activeFilterCount: ReturnType<typeof useDashboardAnalyticsTab>["activeFilterCount"]; autoRefreshInterval: ReturnType<typeof useDashboardAnalyticsTab>["autoRefreshInterval"]; setAutoRefreshInterval: ReturnType<typeof useDashboardAnalyticsTab>["setAutoRefreshInterval"]; handleRefreshAll: ReturnType<typeof useDashboardAnalyticsTab>["handleRefreshAll"]; setShowConfig: ReturnType<typeof useDashboardAnalyticsTab>["setShowConfig"]; showConfig: ReturnType<typeof useDashboardAnalyticsTab>["showConfig"]; exporting: boolean; exportSummaryCSV: ReturnType<typeof useDashboardAnalyticsTab>["exportSummaryCSV"]; summaryData: ReturnType<typeof useDashboardAnalyticsTab>["summaryData"] }) {
  return (<div className="dashboard-toolbar flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:px-4">
    <div className="min-w-0">
      <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{periodLabel}<InfoTooltip interactive title="Período, moneda, sede y corte" description="Ventas y cobros usan el período seleccionado; deudas, existencias y fondos muestran la situación actual. Se consulta una moneda sin conversión automática. Todas las sedes compara sin cambiar la sede operativa." /></p>
      <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
        <Clock className="h-3 w-3" />
        {isUpdatingAny ? "Actualizando datos…" : summaryError ? "No se pudo actualizar" : minutesSinceUpdate === 0 ? "Actualizado recién" : `Actualizado hace ${minutesSinceUpdate} min`}
        <span aria-hidden="true">·</span>
        {currency || activeCurrency}
      </p>
    </div>
    <div className="dashboard-toolbar-actions flex flex-wrap items-center gap-2">
      <button
        ref={filterButtonRef}
        type="button"
        onClick={() => { setShowFilters(open => !open); setCategoryDropdownOpen(false); }}
        aria-expanded={showFilters}
        aria-controls="dashboard-filter-panel"
        className={`dashboard-filter-toggle inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold transition ${showFilters ? "border-teal-500 bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200" : "border-slate-200 bg-white text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"}`}
      >
        <Filter className="h-3.5 w-3.5" />
        Filtros
        {activeFilterCount > 0 && <span className="rounded-md bg-teal-700 px-1.5 py-0.5 text-[10px] text-white">{activeFilterCount}</span>}
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showFilters ? "rotate-180" : ""}`} />
      </button>

      <div className="flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-300">
        <span>Auto-refresco:</span>
        <CustomSelect
          value={autoRefreshInterval}
          onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
          aria-label="Frecuencia de auto-refresco"
          className="bg-transparent font-semibold outline-none cursor-pointer"
        >
          <option value={0}>Manual</option>
          <option value={2}>2 min</option>
          <option value={5}>5 min</option>
        </CustomSelect>
      </div>

      <button
        type="button"
        onClick={handleRefreshAll}
        disabled={isUpdatingAny}
        aria-label="Refrescar métricas"
        className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-teal-500 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
      >
        <RefreshCw className={`h-3.5 w-3.5 ${isUpdatingAny ? "animate-spin text-teal-600" : ""}`} />
        Refrescar
      </button>

      <button
        type="button"
        onClick={() => setShowConfig(!showConfig)}
        aria-expanded={showConfig}
        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-teal-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
      >
        <Layers className="h-3.5 w-3.5 text-teal-600" />
        Paneles
      </button>

      <button
        type="button"
        onClick={exportSummaryCSV}
        disabled={!summaryData || Boolean(summaryError) || isUpdatingAny || exporting}
        title="Descarga un ZIP con tablas en CSV (indicadores, documentos, productos, clientes, vendedores, inventario y alertas)"
        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus-visible:outline focus-visible:outline-teal-400 disabled:opacity-50"
      >
        <Download className="h-3.5 w-3.5" />
        {exporting ? "Exportando…" : "Exportar datos"}
      </button>
    </div>
  </div>);
}
