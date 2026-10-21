import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { X, SlidersHorizontal } from "lucide-react";

export function Panel2({ visiblePanels, setVisiblePanels, setShowConfig }: { visiblePanels: ReturnType<typeof useDashboardAnalyticsTab>["visiblePanels"]; setVisiblePanels: ReturnType<typeof useDashboardAnalyticsTab>["setVisiblePanels"]; setShowConfig: ReturnType<typeof useDashboardAnalyticsTab>["setShowConfig"] }) {
  return (<div className="mt-4 rounded-2xl border border-slate-200/90 bg-white/95 p-6 sm:p-7 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
    <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
      <div className="flex items-center gap-2.5">
        <SlidersHorizontal className="h-4.5 w-4.5 text-teal-600 dark:text-teal-400" />
        <p className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
          Personalizar visibilidad de paneles
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => {
            const allActive = Object.entries(visiblePanels).filter(([key]) => key !== "stats").every(([, value]) => Boolean(value));
            setVisiblePanels({
              summary: !allActive,
              trend: !allActive,
              products: !allActive,
              sellers: !allActive,
              customers: !allActive,
              inventory: !allActive,
              stats: false,
            });
          }}
          className="text-xs font-semibold text-teal-600 hover:text-teal-700 dark:text-teal-400 dark:hover:text-teal-300 transition-colors"
        >
          {Object.entries(visiblePanels).filter(([key]) => key !== "stats").every(([, value]) => Boolean(value)) ? "Ocultar todos" : "Mostrar todos"}
        </button>
        <button
          type="button"
          onClick={() => setShowConfig(false)}
          className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
          aria-label="Cerrar personalización"
        >
          <X className="h-3.5 w-3.5" />
          <span>Cerrar</span>
        </button>
      </div>
    </div>

    <div className="mt-4 flex flex-wrap gap-3">
      {(["summary", "trend", "products", "sellers", "customers", "inventory"] as const).map((key) => {
        const labels: Record<string, string> = {
          summary: "Resumen Ejecutivo",
          trend: "Tendencia Temporal",
          products: "Productos y Margen",
          sellers: "Equipo de Ventas",
          customers: "Cartera de Clientes",
          inventory: "Inventario actual"
        };
        return (
          <label
            key={key}
            className={`group inline-flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-xs font-medium transition-all duration-150 cursor-pointer select-none ${visiblePanels[key]
              ? "border-teal-500/40 bg-teal-500/10 text-slate-900 dark:border-teal-500/40 dark:bg-teal-500/15 dark:text-white shadow-xs"
              : "border-slate-200/80 bg-slate-50 text-slate-600 hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-white"
              }`}
          >
            <input
              type="checkbox"
              checked={visiblePanels[key]}
              onChange={(e) => setVisiblePanels((prev: any) => ({ ...prev, [key]: e.target.checked }))}
              className="sr-only"
            />
            <span
              aria-hidden="true"
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${visiblePanels[key]
                ? "bg-teal-600 dark:bg-teal-500 shadow-xs shadow-teal-500/30"
                : "bg-slate-300 dark:bg-slate-700"
                }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${visiblePanels[key] ? "translate-x-4" : "translate-x-0"
                  }`}
              />
            </span>
            <span className="truncate pr-1">{labels[key]}</span>
          </label>
        );
      })}
    </div>
  </div>);
}
