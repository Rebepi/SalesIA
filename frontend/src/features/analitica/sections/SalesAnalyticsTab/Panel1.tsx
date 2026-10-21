import type { useSalesAnalyticsTab } from "../../hooks/useSalesAnalyticsTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";

export function Panel1({ setBreakdownTab, breakdownTab, period, setPeriod, granularity, setGranularity }: { setBreakdownTab: ReturnType<typeof useSalesAnalyticsTab>["setBreakdownTab"]; breakdownTab: ReturnType<typeof useSalesAnalyticsTab>["breakdownTab"]; period: ReturnType<typeof useSalesAnalyticsTab>["period"]; setPeriod: ReturnType<typeof useSalesAnalyticsTab>["setPeriod"]; granularity: ReturnType<typeof useSalesAnalyticsTab>["granularity"]; setGranularity: ReturnType<typeof useSalesAnalyticsTab>["setGranularity"] }) {
  return (<div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-700/50 bg-slate-800/60 px-4 py-3 shadow-sm">
    <div className="flex flex-wrap gap-1.5">
      {(["day", "product", "branch", "seller"] as const).map((tab) => (
        <button
          key={tab}
          id={`tab-sales-${tab}`}
          onClick={() => setBreakdownTab(tab)}
          className={`rounded-lg px-3.5 py-1.5 text-sm font-semibold transition active:scale-95 ${breakdownTab === tab
            ? "bg-teal-600 text-white shadow-md shadow-teal-900/30"
            : "bg-slate-700/70 text-slate-300 hover:bg-slate-600/80 hover:text-slate-100 border border-slate-600/60"
            }`}
        >
          {tab === "day" ? "Desglose por Día" : tab === "product" ? "Por Producto" : tab === "branch" ? "Por Sucursal" : "Por Vendedor"}
        </button>
      ))}
    </div>

    <div className="flex items-center gap-2">
      <label htmlFor="sales-period-select" className="sr-only">Período</label>
      <CustomSelect
        id="sales-period-select"
        value={period}
        onChange={(e) => setPeriod(e.target.value)}
        className="rounded-lg border border-slate-600/70 bg-slate-700/80 px-3 py-1.5 text-sm text-slate-200 focus:border-teal-500 focus:outline-none"
      >
        <option value="7d">Últimos 7 días</option>
        <option value="30d">Últimos 30 días</option>
        <option value="90d">Últimos 90 días</option>
        <option value="12m">Últimos 12 meses</option>
      </CustomSelect>

      <label htmlFor="sales-granularity-select" className="sr-only">Granularidad</label>
      <CustomSelect
        id="sales-granularity-select"
        value={granularity}
        onChange={(e) => setGranularity(e.target.value)}
        className="rounded-lg border border-slate-600/70 bg-slate-700/80 px-3 py-1.5 text-sm text-slate-200 focus:border-teal-500 focus:outline-none"
      >
        <option value="day">Por Día</option>
        <option value="week">Por Semana</option>
        <option value="month">Por Mes</option>
      </CustomSelect>
    </div>
  </div>);
}
