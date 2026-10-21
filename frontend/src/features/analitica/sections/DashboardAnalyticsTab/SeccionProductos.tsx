import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RefreshCw, Package, Layers, Award } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { MeasurementDefinitionsDialog } from "../../components/MeasurementDefinitionsDialog";

export function SeccionProductos({ productsLoading, productsError, fetchProducts, productsData }: { productsLoading: ReturnType<typeof useDashboardAnalyticsTab>["productsLoading"]; productsError: ReturnType<typeof useDashboardAnalyticsTab>["productsError"]; fetchProducts: ReturnType<typeof useDashboardAnalyticsTab>["fetchProducts"]; productsData: ReturnType<typeof useDashboardAnalyticsTab>["productsData"] }) {
  return (<article className="flex flex-col rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800/80 dark:bg-slate-900/90 h-[520px] min-w-0 dashboard-ranking-card">
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3.5 dark:border-slate-800">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-500/10 text-teal-600 dark:bg-teal-500/20 dark:text-teal-400 ring-1 ring-teal-500/20 shadow-xs">
          <Package className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white tracking-tight">Productos y Margen Comercial <InfoTooltip title="Productos y margen comercial" description="Clasifica los productos por participación en ventas y muestra el margen comercial calculado con el costo histórico registrado al vender." /></h2>
            {productsLoading && <RefreshCw className="h-3 w-3 animate-spin text-teal-600" />}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1">
            Ventas y margen comercial con costo histórico
          </p>
        </div>
      </div>
      <MeasurementDefinitionsDialog context={productsData?.measurement_context} definitions={productsData?.definitions} title="Productos y margen comercial" label="Definiciones" />
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300 ring-1 ring-slate-200 dark:ring-slate-700/60">
        <Award className="h-3 w-3 text-amber-500" />
        Top 10 productos
      </span>
    </div>

    {productsError ? (
      <div className="my-4 flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-300">
        <span>{productsError}</span>
        <button
          type="button"
          onClick={fetchProducts}
          className="rounded bg-rose-100 px-2 py-0.5 font-semibold text-rose-900 hover:bg-rose-200"
        >
          Reintentar
        </button>
      </div>
    ) : productsLoading && !productsData ? (
      <div className="my-4 space-y-2 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-9 bg-slate-100 rounded dark:bg-slate-800" />
        ))}
      </div>
    ) : !productsData || productsData.items.length === 0 ? (
      <div className="flex flex-1 items-center justify-center p-8 text-center text-xs text-slate-400">
        Sin ventas en este período.
      </div>
    ) : (
      <>
        <div className="mt-3 min-h-0 flex-1 pr-1 pagination-shell">
          <PaginatedTable className="w-full table-fixed text-left text-xs" aria-label="Ranking de productos y rentabilidad">
            <colgroup>
              <col className="w-auto" />
              <col style={{ width: "56px" }} />
              <col style={{ width: "84px" }} />
              <col style={{ width: "86px" }} />
            </colgroup>
            <thead className="sticky top-0 z-10 bg-slate-50/95 dark:bg-slate-800/95 backdrop-blur border-b border-slate-200/80 dark:border-slate-700/80 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <tr>
                <th scope="col" className="py-2.5 px-3">Producto</th>
                <th scope="col" className="py-2.5 px-2 text-right">Unid.</th>
                <th scope="col" className="py-2.5 px-2 text-right">Margen</th>
                <th scope="col" className="py-2.5 px-3 text-right">Part.%</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {productsData.items.map((p, idx) => {
                const marginNum = parseFloat(p.margin_pct || "0") || 0;
                const shareNum = parseFloat(p.share_pct) || 0;
                return (
                  <tr key={p.product_id} className="group hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="py-2.5 px-3 pr-2 min-w-0">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-[10px] font-bold ${idx === 0
                          ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/30"
                          : idx === 1
                            ? "bg-slate-200/70 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300 ring-1 ring-slate-400/20"
                            : idx === 2
                              ? "bg-orange-500/15 text-orange-600 dark:text-orange-400 ring-1 ring-orange-500/30"
                              : "bg-slate-100 text-slate-400 dark:bg-slate-800/80 dark:text-slate-500 font-medium"
                          }`}>
                          {idx + 1}
                        </span>
                        <div className="min-w-0 flex-1 truncate">
                          <p className="font-semibold text-[12px] text-slate-900 dark:text-white truncate group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors" title={`${p.name} (${p.sku})`}>
                            {p.name}
                          </p>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="font-mono text-[9px] bg-slate-100 dark:bg-slate-800 px-1 py-0.2 rounded text-slate-500 dark:text-slate-400 truncate max-w-[90px]">
                              {p.sku}
                            </span>
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 truncate">
                              {p.category}
                            </span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums whitespace-nowrap">
                      <span className="font-semibold text-slate-800 dark:text-slate-200 text-[11px]">
                        {Number(p.units).toLocaleString("es-PE")}
                      </span>
                      <span className="block text-[9px] text-slate-400 font-normal">uds.</span>
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums whitespace-nowrap">
                      {p.margin_pct === null ? <span className="text-[10px] text-slate-500">Restringido</span> : <>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${marginNum >= 40
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/25"
                        : marginNum >= 20
                          ? "bg-teal-500/10 text-teal-600 dark:text-teal-400 ring-1 ring-teal-500/25"
                          : "bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/25"
                        }`}>
                        <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${marginNum >= 40 ? "bg-emerald-500" : marginNum >= 20 ? "bg-teal-500" : "bg-amber-500"
                          }`} />
                        {p.margin_pct}%
                      </span>
                      </>}
                    </td>
                    <td className="py-2.5 px-3 text-right tabular-nums whitespace-nowrap">
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-[11px] font-bold text-slate-800 dark:text-slate-100">
                          {p.share_pct}%
                        </span>
                        <div className="h-1 w-12 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400"
                            style={{ width: `${Math.min(100, Math.max(4, shareNum))}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </PaginatedTable>
        </div>
        {productsData.other_categories && (
          <div className="mt-auto shrink-0 rounded-xl border border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-800/40 p-2.5 px-3 flex items-center justify-between gap-2 shadow-xs">
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-slate-200/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300">
                <Layers className="h-3.5 w-3.5" />
              </div>
              <div className="truncate">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  Otros ({productsData.other_categories.products_count} productos)
                </span>
                <span className="block text-[10px] text-slate-400">Resto del catálogo</span>
              </div>
            </div>
            <div className="flex items-center gap-3 text-[11px] tabular-nums shrink-0">
              <span className="text-slate-500 font-medium">
                {productsData.other_categories.units
                  ? `${Number(productsData.other_categories.units).toLocaleString("es-PE")} uds.`
                  : "—"}
              </span>
              <span className="inline-flex items-center rounded-full bg-slate-200/50 dark:bg-slate-700/50 px-2 py-0.5 text-[10px] font-bold text-slate-600 dark:text-slate-300">
                {productsData.other_categories.margin_pct
                  ? `${productsData.other_categories.margin_pct}% mg.`
                  : "—"}
              </span>
              <span className="font-bold text-slate-900 dark:text-white">
                {productsData.other_categories.share_pct}%
              </span>
            </div>
          </div>
        )}
      </>
    )}
  </article>);
}
