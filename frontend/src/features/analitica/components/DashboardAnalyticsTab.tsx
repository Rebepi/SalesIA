import { Panel1 } from "../sections/DashboardAnalyticsTab/Panel1";
import { Panel2 } from "../sections/DashboardAnalyticsTab/Panel2";
import { Panel3 } from "../sections/DashboardAnalyticsTab/Panel3";
import { SeccionTrend } from "../sections/DashboardAnalyticsTab/SeccionTrend";
import { useDashboardAnalyticsTab, type DashboardBranchContext } from "../hooks/useDashboardAnalyticsTab";
import { ExecutiveOverview, ExecutiveAlerts } from "./ExecutiveOverview";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { ExecutiveHighlights } from "./ExecutiveHighlights";

export function DashboardAnalyticsTab({ branchContext }: { branchContext?: DashboardBranchContext }) {
  const dashboard = useDashboardAnalyticsTab(branchContext);
  const summary = dashboard.summaryError ? null : dashboard.summaryData;
  const navigate = (view: string, key?: string, expectedCount?: number) => {
    if (!summary?.executive?.allowed_views.includes(view)) return;
    if (key && !summary.executive.drilldowns?.[key]) return;
    const evidence = key ? { dashboard_evidence: key, dashboard_period: dashboard.period, dashboard_branch: dashboard.branchId, dashboard_currency: dashboard.activeCurrency, dashboard_category: dashboard.category, dashboard_as_of: summary.executive.as_of, ...(expectedCount !== undefined ? { dashboard_expected: String(expectedCount) } : {}) } : undefined;
    window.dispatchEvent(new CustomEvent("salesia:navigate", { detail: { view, evidence } }));
  };
  return <section id="scr-004-executive-dashboard" data-testid="scr-031-analytics-general" className="dashboard-executive space-y-3" aria-busy={dashboard.summaryLoading}>
    <div id="scr-031-analytics-general" className="hidden" aria-hidden="true" />
    <Panel1 {...dashboard} />
    {dashboard.exportError && <p role="alert" className="text-sm text-rose-600 dark:text-rose-400">{dashboard.exportError}</p>}
    {branchContext?.allBranches && <span className="inline-flex items-center gap-1 rounded-full bg-teal-500/10 px-2 py-1 text-xs font-semibold text-teal-700 dark:text-teal-400">Todas las sedes<InfoTooltip interactive title="Comparación de sedes" description="El dashboard compara todas las sedes. La sede operativa de la barra superior se conserva para registrar operaciones." /></span>}
    {!dashboard.showFilters && Boolean(dashboard.category || dashboard.currency || dashboard.period !== "30d" || (!branchContext && dashboard.branchId)) && <div className="dashboard-active-filters flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs dark:border-slate-800 dark:bg-slate-900"><span className="font-semibold text-slate-500">Aplicados:</span>{!branchContext && dashboard.branchId && <button type="button" onClick={() => dashboard.setBranchId("")} className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">Sede: {dashboard.activeBranchObj?.name || dashboard.branchId.slice(0, 8)} ×</button>}{dashboard.category && <button type="button" onClick={() => dashboard.setCategory("")} className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">Categoría: {dashboard.category} ×</button>}{dashboard.currency && <button type="button" onClick={() => dashboard.setCurrency("")} className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">Moneda: {dashboard.currency} ×</button>}{dashboard.period !== "30d" && <button type="button" onClick={() => dashboard.setPeriod("30d")} className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">{dashboard.periodLabel} ×</button>}<button type="button" onClick={dashboard.handleResetFilters} className="ml-auto font-semibold text-rose-600 dark:text-rose-400">Limpiar filtros</button></div>}
    {dashboard.showConfig && <Panel2 {...dashboard} />}
    <Panel3 {...dashboard} hasActiveFilters={Boolean(dashboard.category || dashboard.currency || dashboard.period !== "30d" || (!branchContext && dashboard.branchId))} />
    {dashboard.summaryError && <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300"><span>{dashboard.summaryError}</span><button type="button" onClick={() => dashboard.fetchSummary()} className="font-semibold underline">Reintentar</button></div>}
    {dashboard.visiblePanels.summary && <ExecutiveOverview summary={summary} loading={dashboard.summaryLoading} formatMoney={dashboard.formatMoney} navigate={navigate} />}
    {!dashboard.summaryLoading && summary && <ExecutiveAlerts summary={summary} navigate={navigate} />}
    {dashboard.visiblePanels.trend && <SeccionTrend {...dashboard} summary={summary} />}
    {!dashboard.summaryLoading && summary && <ExecutiveHighlights summary={summary} products={dashboard.productsData} customers={dashboard.customersData} sellers={dashboard.sellersData} productsLoading={dashboard.productsLoading} customersLoading={dashboard.customersLoading} sellersLoading={dashboard.sellersLoading} productsError={dashboard.productsError} customersError={dashboard.customersError} sellersError={dashboard.sellersError} retryProducts={dashboard.fetchProducts} retryCustomers={dashboard.fetchCustomers} retrySellers={dashboard.fetchSellers} visible={dashboard.visiblePanels} formatMoney={dashboard.formatMoney} navigate={navigate} />}
    {dashboard.chartTooltip && <div className="pointer-events-none fixed z-[9999] rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white shadow-2xl" style={{ left: dashboard.chartTooltip.x + 14, top: dashboard.chartTooltip.y - 60, transform: dashboard.chartTooltip.x > window.innerWidth - 180 ? "translateX(-110%)" : undefined }}><p>{dashboard.chartTooltip.date}</p><p className="mt-1 font-semibold text-teal-400">{dashboard.formatMoney(dashboard.chartTooltip.revenue)}</p><p className="mt-1 text-slate-400">{dashboard.chartTooltip.orders_count} {dashboard.chartTooltip.orders_count === 1 ? "documento" : "documentos"}{dashboard.chartTooltip.isZero ? " · Sin ventas" : ""}</p></div>}
  </section>;
}
