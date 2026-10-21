import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { useId, useState } from "react";
import { Search, RotateCcw, SlidersHorizontal, X } from "lucide-react";
import type { useRefundsWorkspaceTab } from "../../hooks/useRefundsWorkspaceTab";

type Props = Pick<ReturnType<typeof useRefundsWorkspaceTab>, "setSelectedStatus" | "selectedStatus" | "search" | "setSearch" | "currencyFilter" | "setCurrencyFilter" | "dateFrom" | "setDateFrom" | "dateTo" | "setDateTo" | "returnFilter" | "setReturnFilter" | "resetFilters"> & { currencies: string[] };
const field = "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-900";
const statuses = [["ALL", "Todos los estados"], ["solicitado", "Solicitados"], ["aprobado", "Aprobados"], ["enviado", "Enviados a pasarela"], ["pendiente", "Pendientes"], ["confirmado", "Confirmados"], ["requiere_conciliacion", "Requieren conciliación"], ["fallido", "Fallidos"]];

export function Panel1({ setSelectedStatus, selectedStatus, search, setSearch, currencyFilter, setCurrencyFilter, dateFrom, setDateFrom, dateTo, setDateTo, returnFilter, setReturnFilter, resetFilters, currencies }: Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const advancedId = useId();
  const advancedCount = [dateFrom, dateTo, returnFilter].filter(Boolean).length;
  const applied = selectedStatus !== "ALL" || Boolean(search || currencyFilter || dateFrom || dateTo || returnFilter);
  return <section aria-label="Filtros de reembolsos" className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <label className="grid gap-2 text-sm font-medium">Buscar reembolso<div className="relative"><Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" /><input className={`${field} pl-9`} value={search} maxLength={128} placeholder="ID, pago, referencia o motivo" onChange={event => setSearch(event.target.value)} /></div></label>
      <label className="grid gap-2 text-sm font-medium">Estado<CustomSelect className={field} value={selectedStatus} onChange={event => setSelectedStatus(event.target.value)}>{statuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</CustomSelect></label>
      <label className="grid gap-2 text-sm font-medium">Moneda<CustomSelect className={field} value={currencyFilter} onChange={event => setCurrencyFilter(event.target.value)}><option value="">Todas las monedas</option>{currencies.map(code => <option key={code} value={code}>{code}</option>)}</CustomSelect></label>
      <div className="refund-advanced sm:col-span-2 xl:col-span-4"><button type="button" className="refund-advanced-toggle" aria-expanded={advancedOpen} aria-controls={advancedId} onClick={() => setAdvancedOpen(value => !value)}>{advancedOpen ? <X size={16} aria-hidden="true" /> : <SlidersHorizontal size={16} aria-hidden="true" />}<span>{advancedOpen ? "Ocultar filtros" : "Más filtros"}</span>{advancedCount > 0 && <span className="refund-filter-count" aria-label={`${advancedCount} filtros adicionales activos`}>{advancedCount}</span>}</button><div id={advancedId} hidden={!advancedOpen}><div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <label className="grid gap-2 text-sm font-medium">Desde (America/Lima)<input className={field} type="date" value={dateFrom} max={dateTo || undefined} onChange={event => setDateFrom(event.target.value)} /></label>
      <label className="grid gap-2 text-sm font-medium">Hasta inclusive (America/Lima)<input className={field} type="date" value={dateTo} min={dateFrom || undefined} onChange={event => setDateTo(event.target.value)} /></label>
      <label className="grid gap-2 text-sm font-medium">Vínculo con devolución<CustomSelect className={field} value={returnFilter} onChange={event => setReturnFilter(event.target.value)}><option value="">Todos los reembolsos</option><option value="true">Con devolución vinculada</option><option value="false">Sin devolución vinculada</option></CustomSelect></label>
      </div></div></div>
    </div>
    {applied && <div className="flex justify-end"><button type="button" onClick={resetFilters} className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-950/40"><RotateCcw size={16} aria-hidden="true" />Limpiar filtros</button></div>}
  </section>;
}
