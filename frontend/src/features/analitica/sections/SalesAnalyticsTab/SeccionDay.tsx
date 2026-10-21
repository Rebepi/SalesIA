import type { useSalesAnalyticsTab } from "../../hooks/useSalesAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { ChevronRight } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionDay({ salesData, currency, handleDrillDown }: { salesData: ReturnType<typeof useSalesAnalyticsTab>["salesData"]; currency: ReturnType<typeof useSalesAnalyticsTab>["currency"]; handleDrillDown: ReturnType<typeof useSalesAnalyticsTab>["handleDrillDown"] }) {
  return (<div className="pagination-group">
    <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Serie Temporal de Facturación</h2><InfoTooltip title="Serie temporal de facturación" description="Ordena la facturación y la cantidad de pedidos por fecha para revelar evolución, picos y períodos sin ventas." /></div>
    <div className="mt-4 pagination-shell">
      <PaginatedTable className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">Fecha</th>
            <th scope="col" className="px-4 py-3">Pedidos</th>
            <th scope="col" className="px-4 py-3">Facturación Bruta</th>
            <th scope="col" className="px-4 py-3">Estado</th>
            <th scope="col" className="px-4 py-3 text-right">Drill-down</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {salesData?.series && salesData.series.length > 0 ? (
            salesData.series.map((row) => (
              <tr key={row.date} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{row.date}</td>
                <td className="px-4 py-3 tabular-nums">{row.orders_count}</td>
                <td className="px-4 py-3 tabular-nums font-semibold text-slate-900">{row.revenue} {currency}</td>
                <td className="px-4 py-3 text-xs">
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700">
                    {row.status || "Sin estado"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDrillDown(row.date, "Día", { "Fecha": row.date, "Pedidos": String(row.orders_count), "Facturación": `${row.revenue} ${currency}` })}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800"
                  >
                    Ver detalle <ChevronRight className="h-3 w-3" />
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} className="py-8 text-center text-sm text-slate-500">
                No hay registros de ventas en el período seleccionado.
              </td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
