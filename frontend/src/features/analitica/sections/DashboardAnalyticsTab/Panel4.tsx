import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { TrendingUp, TrendingDown, ShoppingCart, Users, BarChart2 } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function Panel4({ setDrillDown, formatMoney, summaryData, period }: { setDrillDown: ReturnType<typeof useDashboardAnalyticsTab>["setDrillDown"]; formatMoney: ReturnType<typeof useDashboardAnalyticsTab>["formatMoney"]; summaryData: NonNullable<ReturnType<typeof useDashboardAnalyticsTab>["summaryData"]>; period: ReturnType<typeof useDashboardAnalyticsTab>["period"] }) {
  return (<div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    <article
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-label="Ver desglose de ventas netas"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setDrillDown({
            title: "Desglose Contable de Facturación",
            subtitle: "Composición de ventas netas, ventas brutas, impuestos y devoluciones deducidas",
            rows: [
              { label: "Ventas Netas", value: formatMoney(summaryData.net_revenue || summaryData.total_revenue) },
              { label: "Ventas Brutas", value: formatMoney(summaryData.gross_revenue || summaryData.total_revenue) },
              { label: "Tributos Reconocidos", value: formatMoney(summaryData.tax_amount || "0.00") },
              { label: "Devoluciones Deducidas", value: formatMoney(summaryData.refunds_amount || "0.00"), note: "Reembolsos en estado confirmado/aprobado" }
            ]
          });
        }
      }}
      onClick={() =>
        setDrillDown({
          title: "Desglose Contable de Facturación",
          subtitle: "Composición de ventas netas, ventas brutas, impuestos y devoluciones deducidas",
          rows: [
            { label: "Ventas Netas", value: formatMoney(summaryData.net_revenue || summaryData.total_revenue) },
            { label: "Ventas Brutas", value: formatMoney(summaryData.gross_revenue || summaryData.total_revenue) },
            { label: "Tributos Reconocidos", value: formatMoney(summaryData.tax_amount || "0.00") },
            { label: "Devoluciones Deducidas", value: formatMoney(summaryData.refunds_amount || "0.00"), note: "Reembolsos en estado confirmado/aprobado" }
          ]
        })
      }
      className="group cursor-pointer rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-400 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-center justify-between">
        <div className="rounded-xl bg-teal-50 p-2.5 text-teal-600 dark:bg-teal-950 dark:text-teal-400">
          <TrendingUp className="h-5 w-5" />
        </div>
        {period !== "all" && summaryData.comparative_period && (
          summaryData.comparative_period.has_prior_data && summaryData.comparative_period.delta_revenue_pct ? (
            <span
              title={`Período anterior: ${formatMoney(summaryData.comparative_period.previous_revenue)}`}
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${summaryData.comparative_period.delta_revenue_pct.startsWith("+")
                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                : "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                }`}
            >
              {summaryData.comparative_period.delta_revenue_pct.startsWith("+") ? (
                <TrendingUp className="h-3 w-3" aria-hidden="true" />
              ) : (
                <TrendingDown className="h-3 w-3" aria-hidden="true" />
              )}
              <span>{summaryData.comparative_period.delta_revenue_pct}%</span>
            </span>
          ) : (
            <span
              title={summaryData.comparative_period.previous_revenue ? `Período anterior: ${formatMoney(summaryData.comparative_period.previous_revenue)}` : "Sin transacciones en el período anterior"}
              className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400"
            >
              Sin datos previos
            </span>
          )
        )}
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Ventas Netas <InfoTooltip title="Ventas netas" description="Facturación confirmada del período después de restar las devoluciones aprobadas." /></p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
        {formatMoney(summaryData.net_revenue || summaryData.total_revenue)}
      </p>
      <p className="mt-2 text-[11px] text-slate-400 group-hover:text-teal-600 dark:group-hover:text-teal-400">
        Clic para ver desglose contable →
      </p>
    </article>

    <article
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-label="Ver desglose de pedidos"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setDrillDown({
            title: "Desglose de Pedidos y Ventas",
            subtitle: "Documentos confirmados y ventas no asignadas a un vendedor",
            rows: [
              { label: "Total Documentos", value: String(summaryData.orders_count) },
              { label: "Ventas Sin Vendedor", value: String(summaryData.unassigned_sales?.orders_count || 0) },
              { label: "Importe Sin Vendedor", value: formatMoney(summaryData.unassigned_sales?.revenue || "0.00") }
            ]
          });
        }
      }}
      onClick={() =>
        setDrillDown({
          title: "Desglose de Pedidos y Ventas",
          subtitle: "Documentos confirmados y ventas no asignadas a un vendedor",
          rows: [
            { label: "Total Documentos", value: String(summaryData.orders_count) },
            { label: "Ventas Sin Vendedor", value: String(summaryData.unassigned_sales?.orders_count || 0) },
            { label: "Importe Sin Vendedor", value: formatMoney(summaryData.unassigned_sales?.revenue || "0.00") }
          ]
        })
      }
      className="group cursor-pointer rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-400 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-center justify-between">
        <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
          <ShoppingCart className="h-5 w-5" />
        </div>
        {period !== "all" && summaryData.comparative_period?.delta_orders_pct && (
          <span
            title={`Pedidos previo: ${summaryData.comparative_period.previous_orders_count}`}
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${summaryData.comparative_period.delta_orders_pct.startsWith("+")
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
              : "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
              }`}
          >
            {summaryData.comparative_period.delta_orders_pct.startsWith("+") ? (
              <TrendingUp className="h-3 w-3" aria-hidden="true" />
            ) : (
              <TrendingDown className="h-3 w-3" aria-hidden="true" />
            )}
            <span>{summaryData.comparative_period.delta_orders_pct}%</span>
          </span>
        )}
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Documentos Confirmados <InfoTooltip title="Documentos confirmados" description="Cantidad de comprobantes de venta confirmados o pagados dentro del período." /></p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
        {summaryData.orders_count.toLocaleString("es-PE")}
      </p>
      <p className="mt-2 text-[11px] text-slate-400 group-hover:text-teal-600 dark:group-hover:text-teal-400">
        Excluye borradores y anulaciones →
      </p>
    </article>

    <article
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-label="Ver desglose de clientes activos"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setDrillDown({
            title: "Desglose de Clientes y Productos",
            subtitle: "Compradores en el período vs catálogo total registrado",
            rows: [
              { label: "Clientes con compras en período", value: String(summaryData.active_purchasing_customers ?? summaryData.active_customers) },
              { label: "Clientes registrados activos", value: String(summaryData.active_customers) },
              { label: "Productos activos en catálogo", value: String(summaryData.active_products) }
            ]
          });
        }
      }}
      onClick={() =>
        setDrillDown({
          title: "Desglose de Clientes y Productos",
          subtitle: "Compradores en el período vs catálogo total registrado",
          rows: [
            { label: "Clientes con compras en período", value: String(summaryData.active_purchasing_customers ?? summaryData.active_customers) },
            { label: "Clientes registrados activos", value: String(summaryData.active_customers) },
            { label: "Productos activos en catálogo", value: String(summaryData.active_products) }
          ]
        })
      }
      className="group cursor-pointer rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-400 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-center justify-between">
        <div className="rounded-xl bg-amber-50 p-2.5 text-amber-600 dark:bg-amber-950 dark:text-amber-400">
          <Users className="h-5 w-5" />
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          Registrados: {summaryData.active_customers}
        </span>
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Clientes con Compras <InfoTooltip title="Clientes con compras" description="Número de clientes distintos que registraron al menos una compra confirmada en el período." /></p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
        {(summaryData.active_purchasing_customers ?? summaryData.active_customers).toLocaleString("es-PE")}
      </p>
      <p className="mt-2 text-[11px] text-slate-400 group-hover:text-teal-600 dark:group-hover:text-teal-400">
        {summaryData.active_products} productos registrados →
      </p>
    </article>

    <article
      role="button"
      tabIndex={0}
      aria-haspopup="dialog"
      aria-label="Ver desglose de ticket medio y mediano"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          setDrillDown({
            title: "Desglose de Ticket de Venta",
            subtitle: "Media aritmética vs mediana estadística y rango muestral",
            rows: [
              { label: "Ticket Medio (Promedio)", value: formatMoney(summaryData.average_ticket) },
              { label: "Ticket Mediano (Robusto)", value: formatMoney(summaryData.median_ticket) },
              { label: "Ticket Mínimo", value: formatMoney(summaryData.distribution.min) },
              { label: "Ticket Máximo", value: formatMoney(summaryData.distribution.max) }
            ]
          });
        }
      }}
      onClick={() =>
        setDrillDown({
          title: "Desglose de Ticket de Venta",
          subtitle: "Media aritmética vs mediana estadística y rango muestral",
          rows: [
            { label: "Ticket Medio (Promedio)", value: formatMoney(summaryData.average_ticket) },
            { label: "Ticket Mediano (Robusto)", value: formatMoney(summaryData.median_ticket) },
            { label: "Ticket Mínimo", value: formatMoney(summaryData.distribution.min) },
            { label: "Ticket Máximo", value: formatMoney(summaryData.distribution.max) }
          ]
        })
      }
      className="group cursor-pointer rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-400 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-center justify-between">
        <div className="rounded-xl bg-teal-50 p-2.5 text-teal-600 dark:bg-teal-950 dark:text-teal-400">
          <BarChart2 className="h-5 w-5" />
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          Mediana: {formatMoney(summaryData.median_ticket)}
        </span>
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Ticket Promedio <InfoTooltip align="right" title="Ticket promedio" description="Venta neta dividida entre la cantidad de documentos confirmados del período." /></p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
        {formatMoney(summaryData.average_ticket)}
      </p>
      <p className="mt-2 text-[11px] text-slate-400 group-hover:text-teal-600 dark:group-hover:text-teal-400">
        Clic para ver distribución →
      </p>
    </article>
  </div>);
}
