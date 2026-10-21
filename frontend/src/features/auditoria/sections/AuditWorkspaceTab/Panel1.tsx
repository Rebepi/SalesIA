import type { useAuditWorkspaceTab } from "../../hooks/useAuditWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { FileText, Search } from "lucide-react";

export function Panel1({ search, setSearch, entityFilter, setEntityFilter, filteredLogs, setSelectedDiff }: { search: ReturnType<typeof useAuditWorkspaceTab>["search"]; setSearch: ReturnType<typeof useAuditWorkspaceTab>["setSearch"]; entityFilter: ReturnType<typeof useAuditWorkspaceTab>["entityFilter"]; setEntityFilter: ReturnType<typeof useAuditWorkspaceTab>["setEntityFilter"]; filteredLogs: ReturnType<typeof useAuditWorkspaceTab>["filteredLogs"]; setSelectedDiff: ReturnType<typeof useAuditWorkspaceTab>["setSelectedDiff"] }) {
  return (<div className="pagination-group">
    <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por actor, acción o Trace ID..."
          className="w-72 rounded-xl border border-slate-200 py-1.5 pl-9 pr-3 text-xs text-slate-800"
        />
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="filter-audit-entity" className="text-xs font-semibold text-slate-600">Entidad:</label>
        <CustomSelect
          id="filter-audit-entity"
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-700"
        >
          <option value="all">Todas las entidades</option>
          <option value="sale">Ventas (Sale)</option>
          <option value="product">Productos (Product)</option>
          <option value="customer">Clientes (Customer)</option>
          <option value="user">Usuarios (User)</option>
        </CustomSelect>
      </div>
    </div>

    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-50 font-semibold uppercase text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">Fecha UTC</th>
            <th scope="col" className="px-4 py-3">Actor</th>
            <th scope="col" className="px-4 py-3">Acción</th>
            <th scope="col" className="px-4 py-3">Entidad</th>
            <th scope="col" className="px-4 py-3">Correlación (Trace ID)</th>
            <th scope="col" className="px-4 py-3 text-right">Diff Redactado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filteredLogs.map((log) => (
            <tr key={log.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 font-mono text-slate-500">{log.created_at}</td>
              <td className="px-4 py-3 font-medium text-slate-900">{log.actor_email}</td>
              <td className="px-4 py-3">
                <span className="rounded-md bg-slate-100 px-2 py-0.5 font-mono font-semibold text-slate-800">
                  {log.action}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="font-semibold text-slate-800">{log.entity_type}</span>
                <span className="block font-mono text-[10px] text-slate-400">{log.entity_id.slice(0, 8)}…</span>
              </td>
              <td className="px-4 py-3 font-mono text-slate-600">{log.trace_id}</td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => setSelectedDiff(log)}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-teal-700 hover:bg-slate-50"
                >
                  <FileText className="h-3 w-3" />
                  Ver Diff
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
