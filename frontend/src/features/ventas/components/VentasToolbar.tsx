import { IconAction } from "../../../ui/components/primitives/IconAction";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useState } from "react";
import {
  Search,
  Filter,
  RefreshCw,
  Plus,
  Bookmark,
  Columns,
  RotateCcw,
  X,
  SlidersHorizontal,
} from "lucide-react";
import { VentasFilterState, SavedView } from "../types/ventas";

interface VentasToolbarProps {
  canReadCosts?: boolean;
  filter: VentasFilterState;
  onFilterChange: (patch: Partial<VentasFilterState>) => void;
  onResetFilters: () => void;
  onRefresh: () => void;
  loading: boolean;
  canWrite: boolean;
  onOpenNewSale: () => void;
  onExportCSV: () => void;
  onExportExcel: () => void;
  onExportPDF: () => void;
  savedViews: SavedView[];
  selectedViewId: string;
  onSelectSavedView: (view: SavedView) => void;
  onSaveCurrentView: (name: string) => void;
  columnsConfig: Array<{ key: string; label: string; visible: boolean }>;
  onToggleColumn: (key: string) => void;
  onResetColumns?: () => void;
  branches: Array<{ branch_id?: string; id?: string; name: string }>;
  salesReps: Array<{ id: string; full_name: string }>;
  warehouses: Array<{ warehouse_id?: string; id?: string; name: string }>;
  totalsSummary?: {
    page_total: number;
    page_paid: number;
    page_balance: number;
    filter_total: number;
    filter_paid: number;
    filter_balance: number;
    filter_count: number;
  };
  currency?: string;
  kpiBarVisible?: boolean;
  onToggleKpiBar?: (visible: boolean) => void;
  kpiClickable?: boolean;
  onToggleKpiClickable?: (clickable: boolean) => void;
}

export function VentasToolbar({
  canReadCosts = false,
  filter,
  onFilterChange,
  onResetFilters,
  onRefresh,
  loading,
  canWrite,
  onOpenNewSale,
  savedViews,
  selectedViewId,
  onSelectSavedView,
  onSaveCurrentView,
  columnsConfig,
  onToggleColumn,
  onResetColumns,
  branches,
  salesReps,
  warehouses,
  totalsSummary: _totalsSummary,
  currency: _currency = "USD",
  kpiBarVisible = false,
  onToggleKpiBar,
  kpiClickable = true,
  onToggleKpiClickable,
}: VentasToolbarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showColumnsMenu, setShowColumnsMenu] = useState(false);
  const [showViewConfigMenu, setShowViewConfigMenu] = useState(false);
  const [saveViewModalOpen, setSaveViewModalOpen] = useState(false);
  const [newViewName, setNewViewName] = useState("");

  const activeFiltersCount = [
    filter.date_shortcut !== "all",
    Boolean(filter.date_from || filter.date_to),
    Boolean(filter.customer_id),
    Boolean(filter.sales_rep_id),
    Boolean(filter.branch_id),
    Boolean(filter.warehouse_id),
    Boolean(filter.document_type),
    Boolean(filter.currency),
    Boolean(filter.document_status),
    Boolean(filter.payment_status),
    Boolean(filter.delivery_status),
    Boolean(filter.sunat_status),
    Boolean(filter.return_status),
    Boolean(filter.payment_method),
    Boolean(filter.min_amount || filter.max_amount),
    filter.only_with_balance,
    filter.only_overdue,
    filter.only_with_returns,
    Boolean(filter.origin),
    Boolean(filter.only_zero_cost),
    Boolean(filter.only_unassigned),
    Boolean(filter.only_with_lines),
    Boolean(filter.category),
    Boolean(filter.dashboard_period),
  ].filter(Boolean).length;

  return (
    <div className="space-y-2 w-full">
      <div className="flex flex-wrap items-center justify-between gap-2.5 sm:gap-3 rounded-xl sm:rounded-2xl border border-slate-200 bg-white px-3 sm:px-4 py-2 sm:py-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-900 w-full">
        <div className="flex flex-1 items-center gap-2 min-w-[280px]">
          <div className="relative flex-1 max-w-md">
            <Search className="pointer-events-none absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              aria-label="Buscar ventas"
              placeholder="Buscar por documento, cliente, RUC, DNI, SKU o monto..."
              value={filter.search}
              onChange={(e) => onFilterChange({ search: e.target.value })}
              className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-10 pr-4 text-xs text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-teal-500 focus:ring-4 focus:ring-teal-500/15 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500"
            />
            {filter.search && (
              <button
                type="button"
                onClick={() => onFilterChange({ search: "" })}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-semibold transition ${
              showAdvanced || activeFiltersCount > 0
                ? "border-teal-500 bg-teal-50 text-teal-800 dark:border-teal-400 dark:bg-teal-950/40 dark:text-teal-300"
                : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            <span>Filtros</span>
            {activeFiltersCount > 0 && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-teal-600 text-[10px] font-bold text-white">
                {activeFiltersCount}
              </span>
            )}
          </button>

          {activeFiltersCount > 0 && (
            <IconAction label="Restablecer filtros" tone="neutral"  onClick={onResetFilters}><RotateCcw className="h-4 w-4" /></IconAction>
          )}

          {savedViews.length > 0 && (
            <div className="relative">
              <select
                aria-label="Vistas guardadas"
                value={selectedViewId}
                onChange={(e) => {
                  const found = savedViews.find((v) => v.id === e.target.value);
                  if (found) onSelectSavedView(found);
                }}
                className="rounded-xl border border-slate-200 bg-white py-2 pl-3 pr-8 text-xs font-semibold text-slate-700 outline-none transition focus:border-teal-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
              >
                {savedViews.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <IconAction label="Guardar vista actual" tone="neutral"  onClick={() => setSaveViewModalOpen(true)}><Bookmark className="h-4 w-4" /></IconAction>
        </div>

        <div className="flex items-center gap-2">
          <IconAction label="Actualizar lista" tone="neutral"  onClick={onRefresh} disabled={loading}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-teal-600" : ""}`} /></IconAction>

          <div className="relative">
            <button
              type="button"
              onClick={() => setShowColumnsMenu(!showColumnsMenu)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <Columns className="h-3.5 w-3.5" />
              <span>Columnas</span>
            </button>
            {showColumnsMenu && (
              <div className="absolute right-0 top-11 z-30 w-56 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Visibilidad de columnas
                  </span>
                  {onResetColumns && (
                    <button
                      type="button"
                      onClick={onResetColumns}
                      className="text-[11px] font-semibold text-teal-600 transition hover:text-teal-700 hover:underline dark:text-teal-400"
                    >
                      Restablecer
                    </button>
                  )}
                </div>
                <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                  {columnsConfig.map((col) => (
                    <label
                      key={col.key}
                      className="flex cursor-pointer items-center gap-2 rounded-lg p-1.5 text-xs text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                      <input
                        type="checkbox"
                        checked={col.visible}
                        onChange={() => onToggleColumn(col.key)}
                        className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                      />
                      <span>{col.label}</span>
                    </label>
                  ))}
                </div>
                {onResetColumns && (
                  <div className="mt-2.5 border-t border-slate-100 pt-2 dark:border-slate-800">
                    <button
                      type="button"
                      onClick={onResetColumns}
                      className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-slate-200 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                    >
                      <RotateCcw className="h-3.5 w-3.5 text-slate-400" />
                      <span>Restablecer por defecto</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="relative">
            <IconAction label={kpiBarVisible ? "Configurar vista · tarjetas activadas" : "Configurar vista · tarjetas desactivadas"} tone={kpiBarVisible ? "primary" : "neutral"} aria-expanded={showViewConfigMenu} onClick={() => setShowViewConfigMenu(!showViewConfigMenu)}><SlidersHorizontal className="h-4 w-4" /></IconAction>
            {showViewConfigMenu && (
              <div className="absolute right-0 top-11 z-30 w-80 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
                      Configuración de Vista
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowViewConfigMenu(false)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="space-y-3">
                  <label className="flex cursor-pointer items-start justify-between gap-3 rounded-xl border border-slate-100 p-3 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/60">
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-slate-800 dark:text-slate-100">
                        Mostrar tarjetas de información (KPIs)
                      </p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Muestra métricas resumen (ventas de hoy, mes, por cobrar, etc.) en la parte superior.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={kpiBarVisible}
                      onChange={(e) => onToggleKpiBar?.(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                  </label>

                  <label
                    className={`flex cursor-pointer items-start justify-between gap-3 rounded-xl border p-3 transition ${
                      kpiBarVisible
                        ? "border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/60"
                        : "border-dashed border-slate-200 opacity-50 cursor-not-allowed dark:border-slate-800"
                    }`}
                  >
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-slate-800 dark:text-slate-100">
                        Tarjetas como botones de filtro
                      </p>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400">
                        Al hacer clic en una tarjeta, se filtra la lista automáticamente.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      disabled={!kpiBarVisible}
                      checked={kpiClickable}
                      onChange={(e) => onToggleKpiClickable?.(e.target.checked)}
                      className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                  </label>
                </div>
              </div>
            )}
          </div>

          {canWrite && (
            <button
              type="button"
              onClick={onOpenNewSale}
              className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-xs font-bold text-white shadow-sm transition hover:bg-teal-800 active:scale-[0.98]"
            >
              <Plus className="h-4 w-4" />
              <span>Nueva venta (POS)</span>
            </button>
          )}
        </div>
      </div>

      {showAdvanced && (
        <div className="rounded-xl sm:rounded-2xl border border-slate-200 bg-slate-50/80 p-3 sm:p-4 shadow-inner dark:border-slate-800 dark:bg-slate-900/60 max-h-[45vh] overflow-y-auto">
          <div className="mb-3 flex items-center justify-between border-b border-slate-200 pb-2 dark:border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
              Filtros detallados
            </span>
            <button
              type="button"
              onClick={onResetFilters}
              className="text-xs font-semibold text-rose-600 hover:underline dark:text-rose-400"
            >
              Limpiar todos los filtros
            </button>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Atajo de fechas
              </label>
              <select
                aria-label="Atajo de fechas"
                value={filter.date_shortcut}
                onChange={(e) => onFilterChange({ date_shortcut: e.target.value as any })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="all">Todas las fechas</option>
                <option value="today">Hoy</option>
                <option value="yesterday">Ayer</option>
                <option value="this_week">Esta semana</option>
                <option value="this_month">Este mes</option>
                <option value="last_30_days">Últimos 30 días</option>
                <option value="custom">Rango personalizado</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Fecha desde
              </label>
              <input
                type="date"
                aria-label="Fecha desde"
                value={filter.date_from}
                onChange={(e) => onFilterChange({ date_from: e.target.value, date_shortcut: "custom" })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Fecha hasta
              </label>
              <input
                type="date"
                aria-label="Fecha hasta"
                value={filter.date_to}
                onChange={(e) => onFilterChange({ date_to: e.target.value, date_shortcut: "custom" })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Tipo comprobante
              </label>
              <select
                aria-label="Tipo comprobante"
                value={filter.document_type}
                onChange={(e) => onFilterChange({ document_type: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los tipos</option>
                <option value="INVOICE">Factura</option>
                <option value="RECEIPT">Boleta de venta</option>
                <option value="SALE_NOTE">Nota de venta (sin valor tributario)</option>
                <option value="NOTA_CREDITO">Nota de crédito</option>
                <option value="NOTA_DEBITO">Nota de débito</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Estado documento
              </label>
              <select
                aria-label="Estado documento"
                value={filter.document_status}
                onChange={(e) => onFilterChange({ document_status: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los estados</option>
                <option value="Borrador">Borrador</option>
                <option value="Confirmada">Confirmada</option>
                <option value="Anulada">Anulada</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Estado cobro
              </label>
              <select
                aria-label="Estado cobro"
                value={filter.payment_status}
                onChange={(e) => onFilterChange({ payment_status: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los cobros</option>
                <option value="Sin cobrar">Sin cobrar</option>
                <option value="Parcial">Cobro parcial</option>
                <option value="Pagada">Pagada</option>
                <option value="Vencida">Vencida</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Estado entrega
              </label>
              <select
                aria-label="Estado entrega"
                value={filter.delivery_status}
                onChange={(e) => onFilterChange({ delivery_status: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todas las entregas</option>
                <option value="Pendiente">Pendiente</option>
                <option value="Parcial">Parcial</option>
                <option value="Entregada">Entregada</option>
                <option value="No aplica">No aplica</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Estado SUNAT
              </label>
              <select
                aria-label="Estado SUNAT"
                value={filter.sunat_status}
                onChange={(e) => onFilterChange({ sunat_status: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos SUNAT</option>
                <option value="No aplica">No aplica</option>
                <option value="Pendiente">Pendiente</option>
                <option value="Aceptado">Aceptado</option>
                <option value="Observado">Observado</option>
                <option value="Rechazado">Rechazado</option>
                <option value="Baja">Baja</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Estado devolución
              </label>
              <select
                aria-label="Estado devolución"
                value={filter.return_status}
                onChange={(e) => onFilterChange({ return_status: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todas devoluciones</option>
                <option value="Sin devolución">Sin devolución</option>
                <option value="Parcial">Devolución parcial</option>
                <option value="Total">Devolución total</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Sede
              </label>
              <CustomSelect remote={{ resource: "branches" }}
                aria-label="Filtrar por sede"
                value={filter.branch_id}
                onChange={(e) => onFilterChange({ branch_id: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todas las sedes</option>
                {branches.map((b) => (
                  <option key={b.branch_id || b.id} value={b.branch_id || b.id}>
                    {b.name}
                  </option>
                ))}
              </CustomSelect>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Vendedor
              </label>
              <CustomSelect remote={{ resource: "sales_reps" }}
                aria-label="Filtrar por vendedor"
                value={filter.sales_rep_id}
                onChange={(e) => onFilterChange({ sales_rep_id: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los vendedores</option>
                {salesReps.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.full_name}
                  </option>
                ))}
              </CustomSelect>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Almacén
              </label>
              <CustomSelect remote={{ resource: "warehouses" }}
                aria-label="Filtrar por almacén"
                value={filter.warehouse_id}
                onChange={(e) => onFilterChange({ warehouse_id: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los almacenes</option>
                {warehouses.map((w) => (
                  <option key={w.warehouse_id || w.id} value={w.warehouse_id || w.id}>
                    {w.name}
                  </option>
                ))}
              </CustomSelect>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Moneda
              </label>
              <select
                aria-label="Filtrar por moneda"
                value={filter.currency}
                onChange={(e) => onFilterChange({ currency: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todas las monedas</option>
                <option value="USD">Dólares (USD)</option>
                <option value="PEN">Soles (PEN)</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Origen de venta
              </label>
              <select
                aria-label="Filtrar por origen"
                value={filter.origin}
                onChange={(e) => onFilterChange({ origin: e.target.value })}
                className="w-full rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              >
                <option value="">Todos los orígenes</option>
                <option value="POS">Punto de venta (POS)</option>
                <option value="Cotización">Cotización convertida</option>
                <option value="Pedido">Pedido convertido</option>
                <option value="Repetida">Venta repetida</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                Monto mín / máx
              </label>
              <div className="flex gap-1.5">
                <input
                  type="number"
                  aria-label="Monto mínimo"
                  placeholder="Mín"
                  value={filter.min_amount}
                  onChange={(e) => onFilterChange({ min_amount: e.target.value })}
                  className="w-1/2 rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                />
                <input
                  type="number"
                  aria-label="Monto máximo"
                  placeholder="Máx"
                  value={filter.max_amount}
                  onChange={(e) => onFilterChange({ max_amount: e.target.value })}
                  className="w-1/2 rounded-xl border border-slate-300 bg-white p-2 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Base de fecha<select aria-label="Base de fecha de ventas" value={filter.date_basis || "created"} onChange={event => onFilterChange({ date_basis: event.target.value as "created" | "confirmed" })} className="mt-2 w-full rounded-xl border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-950"><option value="created">Creación de venta</option><option value="confirmed">Confirmación de venta</option></select></label>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Categoría de producto<input aria-label="Categoría de producto en ventas" value={filter.category || ""} onChange={event => onFilterChange({ category: event.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-950" /></label>
            </div>
            <div className="flex flex-col justify-end gap-2 pt-2">
              {canReadCosts && <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300"><input type="checkbox" checked={Boolean(filter.only_zero_cost)} onChange={event => onFilterChange({ only_zero_cost: event.target.checked })} />Con líneas de costo cero</label>}
              <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300"><input type="checkbox" checked={Boolean(filter.only_unassigned)} onChange={event => onFilterChange({ only_unassigned: event.target.checked })} />Sin vendedor asignado</label>
              <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300"><input type="checkbox" checked={Boolean(filter.only_with_lines)} onChange={event => onFilterChange({ only_with_lines: event.target.checked })} />Con detalle de productos</label>
              <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={filter.only_with_balance}
                  onChange={(e) => onFilterChange({ only_with_balance: e.target.checked })}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span>Solo con saldo pendiente</span>
              </label>

              <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={filter.only_overdue}
                  onChange={(e) => onFilterChange({ only_overdue: e.target.checked })}
                  className="rounded border-slate-300 text-rose-600 focus:ring-rose-500"
                />
                <span>Solo vencidas</span>
              </label>

              <label className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={filter.only_with_returns}
                  onChange={(e) => onFilterChange({ only_with_returns: e.target.checked })}
                  className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                />
                <span>Con devolución</span>
              </label>
            </div>
          </div>
        </div>
      )}



      {saveViewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <div className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Guardar vista personalizada
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Asigna un nombre a esta combinación de filtros para acceder rápidamente.
            </p>
            <input
              type="text"
              aria-label="Nombre de la vista"
              placeholder="Ej: Ventas Lima pendientes"
              value={newViewName}
              onChange={(e) => setNewViewName(e.target.value)}
              className="mt-3 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:border-teal-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setSaveViewModalOpen(false)}
                className="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={!newViewName.trim()}
                onClick={() => {
                  onSaveCurrentView(newViewName.trim());
                  setNewViewName("");
                  setSaveViewModalOpen(false);
                }}
                className="rounded-xl bg-teal-700 px-4 py-1.5 text-xs font-bold text-white hover:bg-teal-800 disabled:opacity-50"
              >
                Guardar vista
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
