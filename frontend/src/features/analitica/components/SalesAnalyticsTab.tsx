import { OperatingPerspectivePanel } from "./OperatingPerspectivePanel";
import { Panel1 } from "../sections/SalesAnalyticsTab/Panel1";
import { SeccionDay } from "../sections/SalesAnalyticsTab/SeccionDay";
import { SeccionProduct } from "../sections/SalesAnalyticsTab/SeccionProduct";
import { SeccionSeller } from "../sections/SalesAnalyticsTab/SeccionSeller";
export type { SalesAnalyticsTabProps } from "../types/SalesAnalyticsTab";
import { useSalesAnalyticsTab } from "../hooks/useSalesAnalyticsTab";
import { PaginatedTable } from "../../../ui/components/PaginatedTable";
import { ChevronRight, X } from "lucide-react";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { SalesAnalyticsTabProps } from "../types/SalesAnalyticsTab";

export function SalesAnalyticsTab({ canWrite: _canWrite = true }: SalesAnalyticsTabProps) {
  const { period, setPeriod, granularity, setGranularity, currency, breakdownTab, setBreakdownTab, error, salesData, products, sellers, branches, drillDownItem, setDrillDownItem, handleDrillDown } = useSalesAnalyticsTab({ canWrite: _canWrite });
  return (
    <div id="scr-032-sales-analytics" data-testid="scr-032-sales-analytics" className="space-y-5">
      <Panel1 setBreakdownTab={setBreakdownTab} breakdownTab={breakdownTab} period={period} setPeriod={setPeriod} granularity={granularity} setGranularity={setGranularity} />

      <OperatingPerspectivePanel />

      {error && (
        <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {breakdownTab === "day" && (
        <SeccionDay salesData={salesData} currency={currency} handleDrillDown={handleDrillDown} />
      )}

      {breakdownTab === "product" && (
        <SeccionProduct products={products} currency={currency} handleDrillDown={handleDrillDown} />
      )}

      {breakdownTab === "seller" && (
        <SeccionSeller sellers={sellers} currency={currency} handleDrillDown={handleDrillDown} />
      )}

      {breakdownTab === "branch" && (
        <div className="pagination-group">
          <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Desglose por Sucursal</h2><InfoTooltip title="Ventas por sucursal" description="Distribuye pedidos y facturación entre las sedes autorizadas para el período seleccionado." /></div>
          <div className="mt-4 pagination-shell"><PaginatedTable className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500"><tr><th className="px-4 py-3">Código</th><th className="px-4 py-3">Sucursal</th><th className="px-4 py-3">Ventas</th><th className="px-4 py-3">Facturación</th><th className="px-4 py-3">Ticket medio</th><th className="px-4 py-3">Participación</th><th className="px-4 py-3 text-right">Drill-down</th></tr></thead><tbody className="divide-y divide-slate-100">{branches.length > 0 ? branches.map((branch) => <tr key={branch.branch_id} className="hover:bg-slate-50"><td className="px-4 py-3 font-mono text-xs text-slate-600">{branch.code}</td><td className="px-4 py-3 font-medium text-slate-900">{branch.name}</td><td className="px-4 py-3 tabular-nums">{branch.sales_count}</td><td className="px-4 py-3 tabular-nums font-semibold">{branch.total_revenue} {currency}</td><td className="px-4 py-3 tabular-nums">{branch.average_ticket ?? "—"}</td><td className="px-4 py-3 tabular-nums">{branch.share_pct}%</td><td className="px-4 py-3 text-right"><button onClick={() => handleDrillDown(branch.name, "Sucursal", { "Código": branch.code, "Ventas": String(branch.sales_count), "Facturación": `${branch.total_revenue} ${currency}`, "Participación": `${branch.share_pct}%` })} className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800">Ver detalle <ChevronRight className="h-3 w-3" /></button></td></tr>) : <tr><td colSpan={7} className="py-8 text-center text-sm text-slate-500">No hay sucursales con ventas en el período seleccionado.</td></tr>}</tbody></PaginatedTable></div>
        </div>
      )}

      {drillDownItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">{drillDownItem.title}</h3>
              <button onClick={() => setDrillDownItem(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">{drillDownItem.subtitle}</p>
            <div className="mt-4 space-y-2">
              {drillDownItem.rows.map((r) => (
                <div key={r.label} className="flex justify-between border-b border-slate-50 py-1.5 text-sm">
                  <span className="text-slate-500">{r.label}:</span>
                  <span className="font-semibold text-slate-800">{r.value}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setDrillDownItem(null)}
                className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
