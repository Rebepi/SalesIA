import type { useInsightsEnterpriseView } from "../../hooks/useInsightsEnterpriseView";
import { CustomSelect } from "../../../../ui/components/CustomSelect";

export function Panel1({ selectedSeverity, setSelectedSeverity, selectedStatus, setSelectedStatus, filteredInsights, displayedInsights }: { selectedSeverity: ReturnType<typeof useInsightsEnterpriseView>["selectedSeverity"]; setSelectedSeverity: ReturnType<typeof useInsightsEnterpriseView>["setSelectedSeverity"]; selectedStatus: ReturnType<typeof useInsightsEnterpriseView>["selectedStatus"]; setSelectedStatus: ReturnType<typeof useInsightsEnterpriseView>["setSelectedStatus"]; filteredInsights: ReturnType<typeof useInsightsEnterpriseView>["filteredInsights"]; displayedInsights: ReturnType<typeof useInsightsEnterpriseView>["displayedInsights"] }) {
  return (<section aria-label="Filtros de insights" className="flex flex-wrap items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
    <div className="flex items-center gap-2">
      <label htmlFor="filter-severity" className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
        Gravedad:
      </label>
      <CustomSelect
        id="filter-severity"
        value={selectedSeverity}
        onChange={(e) => setSelectedSeverity(e.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm focus:border-teal-500 focus:outline-none"
      >
        <option value="all">Todas las gravedades</option>
        <option value="critical">Crítica</option>
        <option value="high">Alta</option>
        <option value="medium">Media</option>
        <option value="low">Baja</option>
      </CustomSelect>
    </div>

    <div className="flex items-center gap-2">
      <label htmlFor="filter-status" className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
        Estado:
      </label>
      <CustomSelect
        id="filter-status"
        value={selectedStatus}
        onChange={(e) => setSelectedStatus(e.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm focus:border-teal-500 focus:outline-none"
      >
        <option value="all">Todos los estados</option>
        <option value="new">Nuevos</option>
        <option value="pending">Pendientes</option>
        <option value="in_review">En revisión</option>
        <option value="resolved">Resueltos</option>
        <option value="dismissed">Descartados</option><option value="snoozed">Pospuestos</option>
      </CustomSelect>
    </div>

    <div className="ml-auto text-xs font-medium text-slate-500">
      Mostrando {filteredInsights.length} de {displayedInsights.length} alertas
    </div>
  </section>);
}
