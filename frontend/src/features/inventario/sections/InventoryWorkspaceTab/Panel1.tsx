import { IconAction } from "../../../../ui/components/primitives/IconAction";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { RefreshCw, Search } from "lucide-react";

export function Panel1({ warehouses, selectedWarehouseId, setSelectedWarehouseId, search, setSearch, setRevision, loading }: { warehouses: ReturnType<typeof useInventoryWorkspaceTab>["warehouses"]; selectedWarehouseId: ReturnType<typeof useInventoryWorkspaceTab>["selectedWarehouseId"]; setSelectedWarehouseId: ReturnType<typeof useInventoryWorkspaceTab>["setSelectedWarehouseId"]; search: ReturnType<typeof useInventoryWorkspaceTab>["search"]; setSearch: ReturnType<typeof useInventoryWorkspaceTab>["setSearch"]; setRevision: ReturnType<typeof useInventoryWorkspaceTab>["setRevision"]; loading: ReturnType<typeof useInventoryWorkspaceTab>["loading"] }) {
  return (<div className="inventory-toolbar flex-shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
    <div className="flex items-center w-full sm:w-auto">
      {warehouses.length > 0 ? (
        <label
          htmlFor="inv-warehouse-filter"
          className="inventory-toolbar-warehouse flex items-center gap-2 rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 h-10 text-xs shadow-sm transition hover:border-slate-300 dark:hover:border-slate-600 cursor-pointer w-full sm:w-auto"
        >
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 shrink-0 select-none">
            Almacén:
          </span>
          <CustomSelect remote={{ resource: "warehouses" }}
            searchable
            id="inv-warehouse-filter"
            value={selectedWarehouseId}
            onChange={e => setSelectedWarehouseId(e.target.value)}
            className="inventory-warehouse-select"
          >
            <option value="">Todos los almacenes</option>
            {warehouses.map(w => (
              <option key={w.warehouse_id} value={w.warehouse_id}>{w.name} ({w.code})</option>
            ))}
          </CustomSelect>
        </label>
      ) : (
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 h-10 text-xs text-slate-400 shadow-sm w-full sm:w-auto">
          <span className="font-semibold text-slate-500 dark:text-slate-400">Almacén:</span>
          <span>Cargando almacenes…</span>
        </div>
      )}
    </div>

    <div className="flex items-center gap-2 w-full sm:w-auto">
      <div className="relative flex-1 sm:w-72">
        <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          placeholder="Filtrar por producto o SKU"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full h-10 rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 py-2 pl-9 pr-3 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 outline-none shadow-sm transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
        />
      </div>
      <IconAction label="Actualizar inventario" tone="neutral" onClick={() => setRevision(r => r + 1)} disabled={loading} aria-label="Actualizar inventario"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : "group-hover:rotate-90 transition-transform"}`} /></IconAction>
    </div>
  </div>);
}
