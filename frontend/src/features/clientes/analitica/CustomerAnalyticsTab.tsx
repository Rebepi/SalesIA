import "./customer-analytics.css";
import { MeasurementDefinitionsDialog } from "../../analitica/components/MeasurementDefinitionsDialog";
import { Download, UserCheck, UserMinus, UserPlus, Users } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { PaginatedTable } from "../../../ui/components/PaginatedTable";
import { useAnaliticaClientes } from "../hooks/useAnaliticaClientes";
import type { CustomerAnalyticsTabProps } from "../types/clientes";
export type { CustomerAnalyticsTabProps } from "../types/clientes";
export function CustomerAnalyticsTab({ canWrite: _canWrite = true }: CustomerAnalyticsTabProps) {
  const { loading, currency, measurement, period, setPeriod, selectedSegment, setSelectedSegment, error, summary, cohorts, filteredCustomers, handleExport } = useAnaliticaClientes();
  return (
    <div id="scr-033-customer-analytics" data-testid="scr-033-customer-analytics" className="space-y-6">
      {loading && <p role="status" className="text-sm text-slate-500">Consultando la selección actual de clientes…</p>}
      <NavbarSectionHeader view="customer_analytics" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">CLIENTES</span>
            <h1 className="text-xl font-bold text-slate-900">Analytics de Clientes y Cohortes</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Segmentos, frecuencia de compra, concentración de Pareto y análisis de retención por cohortes.
          </p>
        </div>

        <div className="customer-analytics-actions flex flex-wrap items-center gap-2">
          <MeasurementDefinitionsDialog context={measurement} definitions={measurement ? { segmentacion: measurement.customer_classification || "", cohortes: measurement.cohort_definition || "" } : undefined} title="Información de indicadores de clientes" label="Información de indicadores" />
          <label htmlFor="customer-period-select" className="sr-only">Período</label>
          <CustomSelect
            id="customer-period-select"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700"
          >
            <option value="30d">Últimos 30 días</option>
            <option value="90d">Últimos 90 días</option>
            <option value="12m">Últimos 12 meses</option>
          </CustomSelect>



          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-700 px-3 py-1.5 text-sm font-semibold text-white hover:bg-teal-800"
          >
            <Download className="h-4 w-4" />
            Exportar Segmentos
          </button>
        </div>
      </NavbarSectionHeader>

      {error && (
        <div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="customer-analytics-kpis grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="customer-analytics-kpi customer-analytics-kpi-teal rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500">Cliente Nuevo <InfoTooltip title="Cliente nuevo" description="Cliente con compras en el período y sin compras confirmadas o pagadas anteriores al inicio del período en la empresa. Puede comprar varias veces y seguir siendo nuevo." interactive /></span>
            <span className="rounded-lg bg-teal-50 p-2 text-teal-700"><UserPlus className="h-5 w-5" /></span>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{summary?.new_customers_count || 0}</p>
          <p className="mt-1 text-xs text-slate-500">Sin compras anteriores al inicio del período.</p>
        </div>

        <div className="customer-analytics-kpi customer-analytics-kpi-blue rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500">Cliente Recurrente <InfoTooltip title="Cliente recurrente" description="Cliente con compras en el período que ya tenía compras confirmadas o pagadas antes de su inicio en la empresa." interactive /></span>
            <span className="rounded-lg bg-blue-50 p-2 text-blue-700"><UserCheck className="h-5 w-5" /></span>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{summary?.recurring_customers_count || 0}</p>
          <p className="mt-1 text-xs text-slate-500">Con compras previas al período seleccionado.</p>
        </div>

        <div className="customer-analytics-kpi customer-analytics-kpi-amber rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500">Cliente Inactivo <InfoTooltip title="Cliente inactivo" description="Cliente sin compras confirmadas o pagadas dentro del período seleccionado. El indicador depende de la ventana elegida, no de un plazo fijo de 60 días." interactive /></span>
            <span className="rounded-lg bg-amber-50 p-2 text-amber-700"><UserMinus className="h-5 w-5" /></span>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{summary?.inactive_customers_count || 0}</p>
          <p className="mt-1 text-xs text-slate-500">Sin compras dentro del período seleccionado.</p>
        </div>

        <div className="customer-analytics-kpi customer-analytics-kpi-purple rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500">Concentración Pareto <InfoTooltip align="right" title="Concentración Pareto" description="Porcentaje de la facturación total generado por el 20 % de clientes con mayor compra." interactive /></span>
            <span className="rounded-lg bg-purple-50 p-2 text-purple-700"><Users className="h-5 w-5" /></span>
          </div>
          <p className="mt-2 text-2xl font-bold text-purple-700">{summary?.top_20_concentration_pct || "0"}%</p>
          <p className="mt-1 text-xs text-slate-500">Top 20% de clientes concentra esta cuota de facturación.</p>
        </div>
      </div>

      <div className="customer-analytics-section pagination-group">
        <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Matriz de Retención por Cohortes Mensuales</h2><InfoTooltip title="Retención por cohortes" description="Agrupa clientes por el mes de su primera compra y muestra qué porcentaje vuelve a comprar en los meses siguientes." /></div>
        <p className="mt-0.5 text-xs text-slate-500">Evolución de recompra según el mes de primera adquisición del cliente.</p>
        <div className="mt-4 pagination-shell">
          <PaginatedTable className="w-full text-center text-xs">
            <thead className="bg-slate-50 font-semibold uppercase text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3 text-left">Cohorte</th>
                <th scope="col" className="px-4 py-3">Tamaño (n)</th>
                <th scope="col" className="px-4 py-3">M0</th>
                <th scope="col" className="px-4 py-3">M+1</th>
                <th scope="col" className="px-4 py-3">M+2</th>
                <th scope="col" className="px-4 py-3">M+3</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cohorts.length > 0 ? cohorts.map((cohort) => (
                <tr key={cohort.cohort}>
                  <td className="px-4 py-3 text-left font-medium text-slate-900">{cohort.cohort}</td>
                  <td className="px-4 py-3 tabular-nums font-semibold">{cohort.size} clientes</td>
                  {[0, 1, 2, 3].map((index) => <td key={index} className={`${index === 0 ? "font-semibold text-slate-900" : "text-slate-600"} px-4 py-3`}>{cohort.retention_pct[index] === null ? "Pendiente" : cohort.retention_pct[index] !== undefined ? `${cohort.retention_pct[index]}%` : "—"}</td>)}
                </tr>
              )) : <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No hay suficientes compras confirmadas para construir cohortes.</td></tr>}
            </tbody>
          </PaginatedTable>
        </div>
      </div>

      <div className="customer-analytics-section pagination-group">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
          <div className="flex items-center gap-2"><h2 className="text-base font-bold text-slate-900">Tabla Explicativa de Cartera de Clientes</h2><InfoTooltip title="Cartera de clientes" description="Detalla pedidos, facturación, recencia y ticket medio de cada cliente para el período y segmento seleccionados." /></div>
          <div className="flex items-center gap-2">
            <label htmlFor="segment-filter" className="text-xs font-semibold text-slate-600">Filtrar por segmento:</label>
            <CustomSelect
              id="segment-filter"
              value={selectedSegment}
              onChange={(e) => setSelectedSegment(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700"
            >
              <option value="all">Todos los segmentos</option>
              <option value="new">Cliente Nuevo</option>
              <option value="recurring">Cliente Recurrente</option>
              <option value="inactive">Cliente Inactivo</option>
            </CustomSelect>
          </div>
        </div>

        <div className="pagination-shell">
          <PaginatedTable className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">Código</th>
                <th scope="col" className="px-4 py-3">Razón Social</th>
                <th scope="col" className="px-4 py-3">Segmento</th>
                <th scope="col" className="px-4 py-3">Pedidos</th>
                <th scope="col" className="px-4 py-3">Facturación Total</th>
                <th scope="col" className="px-4 py-3">Recencia</th>
                <th scope="col" className="px-4 py-3">Ticket Medio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCustomers.length > 0 ? (
                filteredCustomers.map((c) => (
                  <tr key={c.customer_id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{c.code}</td>
                    <td className="px-4 py-3 font-medium text-slate-900">{c.legal_name}</td>
                    <td className="px-4 py-3 text-xs">
                      <span className={`rounded-full px-2.5 py-0.5 font-semibold ${c.customer_type === "new"
                        ? "bg-teal-50 text-teal-700"
                        : c.customer_type === "recurring"
                          ? "bg-blue-50 text-blue-700"
                          : "bg-amber-50 text-amber-700"
                        }`}>
                        {c.customer_type === "new" ? "Nuevo" : c.customer_type === "recurring" ? "Recurrente" : c.customer_type === "final_consumer" ? "Consumidor final" : "Inactivo"}
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular-nums">{c.orders_count}</td>
                    <td className="px-4 py-3 tabular-nums font-semibold text-slate-900">{Number(c.total_revenue).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</td>
                    <td className="px-4 py-3 tabular-nums text-slate-600">
                      {c.recency_days !== null ? `${c.recency_days} días` : "—"}
                    </td>
                    <td className="px-4 py-3 tabular-nums text-slate-600">
                      {c.average_ticket ? `${Number(c.average_ticket).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}` : "—"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-sm text-slate-500">
                    No se encontraron clientes para el segmento seleccionado.
                  </td>
                </tr>
              )}
            </tbody>
          </PaginatedTable>
        </div>
      </div>
    </div>
  );
}
