import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { X, ExternalLink } from "lucide-react";

export function Seccionundefined({ drillDown, setDrillDown, handleNavigateToSales }: { drillDown: NonNullable<ReturnType<typeof useDashboardAnalyticsTab>["drillDown"]>; setDrillDown: ReturnType<typeof useDashboardAnalyticsTab>["setDrillDown"]; handleNavigateToSales: ReturnType<typeof useDashboardAnalyticsTab>["handleNavigateToSales"] }) {
  return (<div
    role="dialog"
    aria-modal="true"
    aria-labelledby="drilldown-title"
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
  >
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h3 id="drilldown-title" className="text-base font-bold text-slate-900 dark:text-white">
            {drillDown.title}
          </h3>
          <p className="text-xs text-slate-500">{drillDown.subtitle}</p>
        </div>
        <button
          type="button"
          onClick={() => setDrillDown(null)}
          aria-label="Cerrar modal de desglose"
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="mt-4 space-y-2.5">
        {drillDown.rows.map((r, i) => (
          <div key={i} className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-800/60">
            <div>
              <span className="text-slate-600 dark:text-slate-300 font-medium">{r.label}</span>
              {r.note && <span className="block text-[10px] text-slate-400">{r.note}</span>}
            </div>
            <span className="font-bold tabular-nums text-slate-900 dark:text-white">{r.value}</span>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
        <button
          type="button"
          onClick={handleNavigateToSales}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-600 hover:text-teal-700 dark:text-teal-400"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Ver ventas detalladas
        </button>
        <button
          type="button"
          onClick={() => setDrillDown(null)}
          className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>);
}
