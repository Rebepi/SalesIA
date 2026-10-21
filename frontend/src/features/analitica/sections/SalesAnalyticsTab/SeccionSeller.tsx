import type { useSalesAnalyticsTab } from "../../hooks/useSalesAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { ChevronRight } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionSeller({ sellers, currency, handleDrillDown }: { sellers: ReturnType<typeof useSalesAnalyticsTab>["sellers"]; currency: ReturnType<typeof useSalesAnalyticsTab>["currency"]; handleDrillDown: ReturnType<typeof useSalesAnalyticsTab>["handleDrillDown"] }) {
  return (<div className="pagination-group">
    <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Rendimiento por Vendedor</h2><InfoTooltip title="Rendimiento por vendedor" description="Compara la cantidad de pedidos y la facturación atribuida a cada integrante del equipo comercial." /></div>
    <div className="mt-4 pagination-shell">
      <PaginatedTable className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">Vendedor</th>
            <th scope="col" className="px-4 py-3">Ventas Cerradas</th>
            <th scope="col" className="px-4 py-3">Facturación Total</th>
            <th scope="col" className="px-4 py-3">Ticket Medio</th>
            <th scope="col" className="px-4 py-3 text-right">Drill-down</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {sellers.length > 0 ? (
            sellers.map((s) => (
              <tr key={s.seller_id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{s.seller_name}</td>
                <td className="px-4 py-3 tabular-nums">{s.sales_count}</td>
                <td className="px-4 py-3 tabular-nums font-semibold text-slate-900">{s.total_revenue} {currency}</td>
                <td className="px-4 py-3 tabular-nums text-slate-600">{s.average_ticket || "—"}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDrillDown(s.seller_name, "Vendedor", { "Ventas": String(s.sales_count), "Facturación": `${s.total_revenue} ${currency}`, "Ticket Medio": s.average_ticket || "N/A" })}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800"
                  >
                    Ver cartera <ChevronRight className="h-3 w-3" />
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} className="py-8 text-center text-sm text-slate-500">
                No hay vendedores activos en el período.
              </td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
