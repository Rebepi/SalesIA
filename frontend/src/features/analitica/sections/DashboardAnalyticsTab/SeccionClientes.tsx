import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RefreshCw, TrendingUp, Users, Building2, Sparkles, RotateCcw } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionClientes({ customersLoading, customersData, customersError, fetchCustomers, getInitials, formatRecency, formatMoney }: { customersLoading: ReturnType<typeof useDashboardAnalyticsTab>["customersLoading"]; customersData: ReturnType<typeof useDashboardAnalyticsTab>["customersData"]; customersError: ReturnType<typeof useDashboardAnalyticsTab>["customersError"]; fetchCustomers: ReturnType<typeof useDashboardAnalyticsTab>["fetchCustomers"]; getInitials: ReturnType<typeof useDashboardAnalyticsTab>["getInitials"]; formatRecency: ReturnType<typeof useDashboardAnalyticsTab>["formatRecency"]; formatMoney: ReturnType<typeof useDashboardAnalyticsTab>["formatMoney"] }) {
  return (<article className="flex flex-col rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-800/80 dark:bg-slate-900/90 h-[520px] min-w-0 dashboard-ranking-card">
    <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-sky-500/10 text-sky-600 dark:bg-sky-500/20 dark:text-sky-400 ring-1 ring-sky-500/20 shadow-xs">
          <Building2 className="h-4 w-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white tracking-tight">Cartera de Clientes <InfoTooltip title="Cartera de clientes" description="Resume los compradores activos, su tipo, recencia y aporte a la facturación del período." /></h2>
            {customersLoading && <RefreshCw className="h-3 w-3 animate-spin text-sky-600" />}
          </div>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1">
            Compradores activos · Recencia y tipología
          </p>
        </div>
      </div>
      {customersData?.summary && (
        <span className="inline-flex items-center gap-1 rounded-full bg-sky-500/10 px-2.5 py-1 text-[10px] font-semibold text-sky-700 dark:bg-sky-500/20 dark:text-sky-300 ring-1 ring-sky-500/30">
          <TrendingUp className="h-3 w-3 text-sky-500" />
          Pareto Top 20%: {customersData.summary.top_20_concentration_pct}%
        </span>
      )}
    </div>

    {customersError ? (
      <div className="my-4 flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-300">
        <span>{customersError}</span>
        <button
          type="button"
          onClick={fetchCustomers}
          className="rounded bg-rose-100 px-2 py-0.5 font-semibold text-rose-900 hover:bg-rose-200"
        >
          Reintentar
        </button>
      </div>
    ) : customersLoading && !customersData ? (
      <div className="my-4 space-y-2 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-9 bg-slate-100 rounded dark:bg-slate-800" />
        ))}
      </div>
    ) : !customersData || customersData.items.length === 0 ? (
      <div className="flex flex-1 items-center justify-center p-8 text-center text-xs text-slate-400">
        Sin clientes con compras en este período.
      </div>
    ) : (
      <>
        <div className="mt-3 min-h-0 flex-1 pr-1 pagination-shell">
          <PaginatedTable className="w-full table-fixed text-left text-xs" aria-label="Cartera de clientes con compras">
            <colgroup>
              <col className="w-auto" />
              <col style={{ width: "90px" }} />
              <col style={{ width: "82px" }} />
              <col style={{ width: "105px" }} />
            </colgroup>
            <thead className="sticky top-0 z-10 bg-slate-50/95 dark:bg-slate-800/95 backdrop-blur border-b border-slate-200/80 dark:border-slate-700/80 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <tr>
                <th scope="col" className="py-2.5 px-3">Cliente</th>
                <th scope="col" className="py-2.5 px-2 text-center">Tipo</th>
                <th scope="col" className="py-2.5 px-2 text-right">Recencia</th>
                <th scope="col" className="py-2.5 px-3 text-right">Facturado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {customersData.items.map((c, idx) => (
                <tr key={c.customer_id} className="group hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="py-2.5 px-3 pr-2 min-w-0">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="relative shrink-0">
                        <div className={`flex h-7 w-7 items-center justify-center rounded-lg text-[10px] font-bold shadow-xs ${idx === 0
                          ? "bg-gradient-to-br from-sky-400 to-sky-600 text-white shadow-sky-500/20"
                          : idx === 1
                            ? "bg-gradient-to-br from-indigo-400 to-indigo-600 text-white shadow-indigo-500/20"
                            : idx === 2
                              ? "bg-gradient-to-br from-purple-400 to-purple-600 text-white shadow-purple-500/20"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                          }`}>
                          {getInitials(c.legal_name)}
                        </div>
                        <span className="absolute -bottom-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-slate-900 text-[8px] font-bold text-white ring-1 ring-white dark:bg-white dark:text-slate-900 dark:ring-slate-900">
                          {idx + 1}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1 truncate">
                        <p className="font-semibold text-[12px] text-slate-900 dark:text-white truncate group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors" title={`${c.legal_name} (${c.code})`}>
                          {c.legal_name}
                        </p>
                        <span className="font-mono text-[9px] bg-slate-100 dark:bg-slate-800 px-1 py-0.2 rounded text-slate-500 dark:text-slate-400">
                          {c.code}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-center whitespace-nowrap">
                    {c.customer_type === "recurring" ? (
                      <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 ring-1 ring-indigo-500/25">
                        <RotateCcw className="h-2.5 w-2.5" />
                        Recurrente
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 ring-1 ring-emerald-500/25">
                        <Sparkles className="h-2.5 w-2.5" />
                        Nuevo
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-2 text-right tabular-nums whitespace-nowrap">
                    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${c.recency_days !== null && c.recency_days <= 7
                      ? "text-emerald-600 dark:text-emerald-400 font-semibold"
                      : c.recency_days !== null && c.recency_days <= 30
                        ? "text-slate-600 dark:text-slate-300"
                        : "text-amber-600 dark:text-amber-400"
                      }`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${c.recency_days !== null && c.recency_days <= 7
                        ? "bg-emerald-500"
                        : c.recency_days !== null && c.recency_days <= 30
                          ? "bg-slate-400"
                          : "bg-amber-500"
                        }`} />
                      {formatRecency(c.recency_days)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right tabular-nums whitespace-nowrap">
                    <span className="font-bold text-slate-900 dark:text-white text-[12px]">
                      {formatMoney(c.total_revenue)}
                    </span>
                    {c.revenue_share_pct && (
                      <span className="block text-[9px] text-slate-400 font-normal">
                        {c.revenue_share_pct}% total
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </PaginatedTable>
        </div>
        {customersData.summary && (
          <div className="mt-auto shrink-0 rounded-xl border border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-800/40 p-2.5 px-3 flex items-center justify-between gap-2 shadow-xs">
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-sky-100/70 dark:bg-sky-950/70 text-sky-600 dark:text-sky-300">
                <Users className="h-3.5 w-3.5" />
              </div>
              <div className="truncate">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  {customersData.summary.active_in_period} compradores activos
                </span>
                <span className="block text-[10px] text-slate-400">
                  {customersData.summary.new_customers_count} nuevos · {customersData.summary.recurring_customers_count} recurrentes
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 text-[11px] tabular-nums shrink-0">
              <span className="inline-flex items-center rounded-full bg-sky-500/10 dark:bg-sky-500/20 px-2 py-0.5 text-[10px] font-bold text-sky-700 dark:text-sky-300 ring-1 ring-sky-500/30">
                Top 20% = {customersData.summary.top_20_concentration_pct}% vtas
              </span>
            </div>
          </div>
        )}
      </>
    )}
  </article>);
}
