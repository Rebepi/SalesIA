import type { useSalesAnalyticsTab } from "../../hooks/useSalesAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { ChevronRight } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionProduct({ products, currency, handleDrillDown }: { products: ReturnType<typeof useSalesAnalyticsTab>["products"]; currency: ReturnType<typeof useSalesAnalyticsTab>["currency"]; handleDrillDown: ReturnType<typeof useSalesAnalyticsTab>["handleDrillDown"] }) {
  return (<div className="pagination-group">
    <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Ventas por Jerarquía de Producto</h2><InfoTooltip title="Ventas por producto" description="Agrupa unidades y facturación según la jerarquía de productos para comparar su contribución comercial." /></div>
    <div className="mt-4 pagination-shell">
      <PaginatedTable className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">SKU</th>
            <th scope="col" className="px-4 py-3">Producto</th>
            <th scope="col" className="px-4 py-3">Unidades</th>
            <th scope="col" className="px-4 py-3">Facturación</th>
            <th scope="col" className="px-4 py-3">Participación</th>
            <th scope="col" className="px-4 py-3 text-right">Drill-down</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {products.length > 0 ? (
            products.map((p) => (
              <tr key={p.product_id || p.sku} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{p.sku}</td>
                <td className="px-4 py-3 font-medium text-slate-900">{p.name}</td>
                <td className="px-4 py-3 tabular-nums">{p.units}</td>
                <td className="px-4 py-3 tabular-nums font-semibold text-slate-900">{p.revenue} {currency}</td>
                <td className="px-4 py-3 tabular-nums text-slate-500">{p.share_pct}%</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDrillDown(p.name, "Producto", { "SKU": p.sku, "Unidades vendidas": p.units, "Ingresos": `${p.revenue} ${currency}`, "Share": `${p.share_pct}%` })}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800"
                  >
                    Ver variantes <ChevronRight className="h-3 w-3" />
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6} className="py-8 text-center text-sm text-slate-500">
                No hay productos registrados en este período.
              </td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
