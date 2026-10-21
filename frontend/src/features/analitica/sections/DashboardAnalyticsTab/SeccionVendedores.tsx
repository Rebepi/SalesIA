import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RefreshCw, Users, CheckCircle2, ChevronDown, ChevronUp, Store } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionVendedores({ sellersLoading, sellersData, sellersError, fetchSellers, displayedSellers, getQuotaColorClasses, getInitials, formatMoney, period, zeroSellers, setShowZeroSellers, showZeroSellers }: { sellersLoading: ReturnType<typeof useDashboardAnalyticsTab>["sellersLoading"]; sellersData: ReturnType<typeof useDashboardAnalyticsTab>["sellersData"]; sellersError: ReturnType<typeof useDashboardAnalyticsTab>["sellersError"]; fetchSellers: ReturnType<typeof useDashboardAnalyticsTab>["fetchSellers"]; displayedSellers: ReturnType<typeof useDashboardAnalyticsTab>["displayedSellers"]; getQuotaColorClasses: ReturnType<typeof useDashboardAnalyticsTab>["getQuotaColorClasses"]; getInitials: ReturnType<typeof useDashboardAnalyticsTab>["getInitials"]; formatMoney: ReturnType<typeof useDashboardAnalyticsTab>["formatMoney"]; period: ReturnType<typeof useDashboardAnalyticsTab>["period"]; zeroSellers: ReturnType<typeof useDashboardAnalyticsTab>["zeroSellers"]; setShowZeroSellers: ReturnType<typeof useDashboardAnalyticsTab>["setShowZeroSellers"]; showZeroSellers: ReturnType<typeof useDashboardAnalyticsTab>["showZeroSellers"] }) {
  return (<article className="flex flex-col rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800/80 dark:bg-slate-900/90 h-[520px] min-w-0 dashboard-ranking-card">
    <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400 ring-1 ring-indigo-500/20 shadow-xs">
          <Users className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white tracking-tight">Rendimiento por Vendedor <InfoTooltip title="Rendimiento por vendedor" description="Compara pedidos, facturación acumulada y cumplimiento de cuota para cada vendedor." /></h2>
            {sellersLoading && <RefreshCw className="h-3 w-3 animate-spin text-indigo-600" />}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1">
            Ventas acumuladas y cumplimiento de cuota
          </p>
        </div>
      </div>
      {sellersData?.reconciliation_checked && (
        <span
          title="La suma de todas las ventas asignadas más las no asignadas concilia al 100% con la facturación total del período."
          className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 ring-1 ring-emerald-500/30 cursor-help"
        >
          <CheckCircle2 className="h-3 w-3 text-emerald-500" />
          Conciliado 100%
        </span>
      )}
    </div>

    {sellersError ? (
      <div className="my-4 flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-300">
        <span>{sellersError}</span>
        <button
          type="button"
          onClick={fetchSellers}
          className="rounded bg-rose-100 px-2 py-0.5 font-semibold text-rose-900 hover:bg-rose-200"
        >
          Reintentar
        </button>
      </div>
    ) : sellersLoading && !sellersData ? (
      <div className="my-4 space-y-2 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-9 bg-slate-100 rounded dark:bg-slate-800" />
        ))}
      </div>
    ) : !sellersData || displayedSellers.length === 0 ? (
      <div className="flex flex-1 items-center justify-center p-8 text-center text-xs text-slate-400">
        Sin vendedores con actividad en este período.
      </div>
    ) : (
      <>
        <div className="mt-3 min-h-0 flex-1 pr-1 pagination-shell">
          <PaginatedTable className="w-full table-fixed text-left text-xs" aria-label="Rendimiento del equipo de vendedores">
            <colgroup>
              <col className="w-auto" />
              <col style={{ width: "54px" }} />
              <col style={{ width: "110px" }} />
              <col style={{ width: "100px" }} />
            </colgroup>
            <thead className="sticky top-0 z-10 bg-slate-50/95 dark:bg-slate-800/95 backdrop-blur border-b border-slate-200/80 dark:border-slate-700/80 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <tr>
                <th scope="col" className="py-2.5 px-3">Vendedor</th>
                <th scope="col" className="py-2.5 px-2 text-right">Ped.</th>
                <th scope="col" className="py-2.5 px-2 text-right">Facturación</th>
                <th scope="col" className="py-2.5 px-3 text-right">Cuota</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {displayedSellers.map((s, idx) => {
                const quotaInfo = getQuotaColorClasses(s.quota_completion_pct);
                const pctVal = s.quota_completion_pct ? parseFloat(s.quota_completion_pct) : null;
                return (
                  <tr key={s.seller_id} className="group hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="py-2.5 px-3 pr-2 min-w-0">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="relative shrink-0">
                          <div className={`flex h-7 w-7 items-center justify-center rounded-lg text-[10px] font-bold shadow-xs ${idx === 0
                            ? "bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-amber-500/20"
                            : idx === 1
                              ? "bg-gradient-to-br from-slate-400 to-slate-600 text-white shadow-slate-500/20"
                              : idx === 2
                                ? "bg-gradient-to-br from-amber-700 to-amber-900 text-white shadow-amber-800/20"
                                : "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/40"
                            }`}>
                            {getInitials(s.seller_name)}
                          </div>
                          <span className="absolute -bottom-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-slate-900 text-[8px] font-bold text-white ring-1 ring-white dark:bg-white dark:text-slate-900 dark:ring-slate-900">
                            {idx + 1}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 truncate">
                          <p className="font-semibold text-[12px] text-slate-900 dark:text-white truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {s.seller_name}
                          </p>
                          <span className="block text-[10px] text-slate-400 dark:text-slate-500 truncate" title={s.seller_email}>
                            {s.seller_email}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums whitespace-nowrap">
                      <span className="font-semibold text-slate-800 dark:text-slate-200 text-[11px]">
                        {s.sales_count}
                      </span>
                      <span className="block text-[9px] text-slate-400 font-normal">ped.</span>
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums whitespace-nowrap">
                      <span className="font-bold text-slate-900 dark:text-white text-[12px]">
                        {formatMoney(s.total_revenue)}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right tabular-nums whitespace-nowrap">
                      {period === "all" ? (
                        <span className="text-[10px] text-slate-400">—</span>
                      ) : pctVal !== null ? (
                        <div className="flex flex-col items-end gap-1">
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold ${pctVal >= 100
                            ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/25"
                            : pctVal >= 50
                              ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/25"
                              : "bg-rose-500/10 text-rose-600 dark:text-rose-400 ring-1 ring-rose-500/25"
                            }`}>
                            {pctVal}%
                          </span>
                          <div className="h-1 w-14 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${quotaInfo.bar}`}
                              style={{ width: `${Math.min(100, Math.max(4, pctVal))}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span className="text-[10px] text-slate-400 italic">Sin cuota</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </PaginatedTable>
        </div>

        <div className="mt-auto shrink-0 space-y-1.5 pt-2">
          {sellersData.unassigned && Number(sellersData.unassigned.sales_count) > 0 && (
            <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-800/40 p-2.5 px-3 flex items-center justify-between gap-2 shadow-xs">
              <div className="flex items-center gap-2 min-w-0">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-slate-200/60 dark:bg-slate-700/60 text-slate-600 dark:text-slate-300">
                  <Store className="h-3.5 w-3.5" />
                </div>
                <div className="truncate">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    Ventas Sin Asignar
                  </span>
                  <span className="block text-[10px] text-slate-400">Autoservicio / canal directo</span>
                </div>
              </div>
              <div className="flex items-center gap-3 text-[11px] tabular-nums shrink-0">
                <span className="text-slate-500 font-medium">
                  {sellersData.unassigned.sales_count} ped.
                </span>
                <span className="font-bold text-slate-900 dark:text-white">
                  {formatMoney(sellersData.unassigned.total_revenue)}
                </span>
              </div>
            </div>
          )}
          {zeroSellers.length > 0 && (
            <div className="flex items-center justify-center pt-0.5">
              <button
                type="button"
                onClick={() => setShowZeroSellers(!showZeroSellers)}
                className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950/50 transition-colors"
              >
                {showZeroSellers
                  ? "Ocultar sin ventas"
                  : `+ ${zeroSellers.length} sin ventas`}
                {showZeroSellers ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            </div>
          )}
        </div>
      </>
    )}
  </article>);
}
