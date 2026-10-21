import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { Activity } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionInventario({ branchId, category, summaryData, formatMoney }: { branchId: ReturnType<typeof useDashboardAnalyticsTab>["branchId"]; category: ReturnType<typeof useDashboardAnalyticsTab>["category"]; summaryData: ReturnType<typeof useDashboardAnalyticsTab>["summaryData"]; formatMoney: ReturnType<typeof useDashboardAnalyticsTab>["formatMoney"] }) {
  return (<article className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 min-w-0">
    <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
      <div className="flex items-center gap-2">
        <Activity className="h-4 w-4 text-teal-600" />
        <h2 className="flex items-center gap-2 text-base font-bold text-slate-900 dark:text-white">Salud del Inventario y Valuación <InfoTooltip title="Salud del inventario" description="Resume el valor de las existencias y señala riesgos de disponibilidad, rotación o diferencias de stock." /></h2>
      </div>
      <span className="text-[10px] font-medium text-slate-400">
        {branchId || category
          ? "Filtros aplicados"
          : "Toda la empresa (sin filtros)"}
      </span>
    </div>

    {summaryData?.inventory_summary ? (
      <div className="mt-4 flex flex-1 flex-col justify-between space-y-4">
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Valuación Total de Existencias</span>
          <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white tabular-nums">
            {summaryData.inventory_summary.valuation_total === null ? "Restringido" : formatMoney(summaryData.inventory_summary.valuation_total)}
          </p>
          <p className="mt-1 text-[11px] text-slate-400">
            Método de costo: {summaryData.inventory_summary.valuation_method}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-950">
            <span className="text-xs text-slate-500">Stock Físico Total</span>
            <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white tabular-nums">
              {Number(summaryData.inventory_summary.total_physical).toLocaleString("es-PE")}
            </p>
            <span className="text-[10px] text-slate-400">
              {summaryData.inventory_summary.has_mixed_units ? "unidades equivalentes" : "unid."}
            </span>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-950">
            <span className="text-xs text-slate-500">Stock Disponible Neto</span>
            <p className="mt-1 text-lg font-bold text-teal-600 dark:text-teal-400 tabular-nums">
              {Number(summaryData.inventory_summary.total_available).toLocaleString("es-PE")}
            </p>
            <span className="text-[10px] text-slate-400">
              {summaryData.inventory_summary.has_mixed_units ? "unidades equivalentes" : "unid."}
            </span>
          </div>
        </div>

        {Number(summaryData.inventory_summary.total_physical) > 0 && (
          <div>
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Disponibilidad inmediata sobre stock físico:</span>
              <strong className="text-slate-800 dark:text-slate-200">
                {(
                  (Number(summaryData.inventory_summary.total_available) /
                    Math.max(1, Number(summaryData.inventory_summary.total_physical))) *
                  100
                ).toFixed(1)}%
              </strong>
            </div>
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <div
                className="h-full bg-teal-600"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(
                      0,
                      (Number(summaryData.inventory_summary.total_available) /
                        Math.max(1, Number(summaryData.inventory_summary.total_physical))) *
                      100
                    )
                  )}%`
                }}
              />
            </div>
          </div>
        )}

        {summaryData.inventory_summary.has_mixed_units &&
          summaryData.inventory_summary.units_breakdown &&
          summaryData.inventory_summary.units_breakdown.length > 0 && (
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-[11px] text-slate-600 dark:border-slate-800 dark:bg-slate-800/40 dark:text-slate-300">
              <span className="font-semibold block mb-1">Desglose por unidad de medida:</span>
              <div className="flex flex-wrap gap-2">
                {summaryData.inventory_summary.units_breakdown.map((ub) => (
                  <span key={ub.unit} className="rounded bg-white px-2 py-0.5 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                    {ub.unit}: <strong>{Number(ub.physical).toLocaleString("es-PE")}</strong> físicos /{" "}
                    <strong>{Number(ub.available).toLocaleString("es-PE")}</strong> disp.
                  </span>
                ))}
              </div>
            </div>
          )}
      </div>
    ) : (
      <p className="p-8 text-center text-xs text-slate-400">{summaryData?.restrictions?.inventory ? "La consulta de existencias requiere permiso de lectura de inventario." : "Sin datos de existencias disponibles."}</p>
    )}
  </article>);
}
