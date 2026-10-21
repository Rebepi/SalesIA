import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Lock, Search, ShieldCheck } from "lucide-react";

export function SeccionSuppliers({ onQualification, search, setSearch, filteredSuppliers, handleViewPerformance }: { onQualification?: (id: string) => void; search: ReturnType<typeof usePurchasesWorkspaceTab>["search"]; setSearch: ReturnType<typeof usePurchasesWorkspaceTab>["setSearch"]; filteredSuppliers: ReturnType<typeof usePurchasesWorkspaceTab>["filteredSuppliers"]; handleViewPerformance: ReturnType<typeof usePurchasesWorkspaceTab>["handleViewPerformance"] }) {
  return (<section id="scr-025-suppliers-tab" className="space-y-4">
    <div className="flex items-center justify-between gap-3">
      <div className="relative w-80">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <input
          placeholder="Buscar por RUC o Razón Social"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-xs outline-none focus:ring-2 focus:ring-teal-200"
        />
      </div>
      <p className="text-xs text-slate-500">Total registrados: {filteredSuppliers.length}</p>
    </div>

    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">RUC / Razón Social</th>
            <th className="px-4 py-3">Contacto</th>
            <th className="px-4 py-3">Plazo Pago</th>
            <th className="px-4 py-3">Moneda</th>
            <th className="px-4 py-3">Banco e Información Financiera</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {filteredSuppliers.map(sup => (
            <tr key={sup.id} className="hover:bg-slate-50/60">
              <td className="px-4 py-3 font-medium text-slate-900">
                <div>{sup.legal_name}</div>
                <span className="font-mono text-[10px] text-slate-400">RUC: {sup.tax_id}</span>
              </td>
              <td className="px-4 py-3 text-slate-600">
                <div>{sup.contact_name || "Sin contacto"}</div>
                <span className="text-[10px] text-slate-400">{sup.email || sup.phone || "—"}</span>
              </td>
              <td className="px-4 py-3 text-slate-700">{sup.payment_terms_days} días</td>
              <td className="px-4 py-3 font-semibold text-slate-700">{sup.currency}</td>
              <td className="px-4 py-3">
                {sup.bank_account ? (
                  <div className="flex items-center gap-1.5 text-slate-700">
                    <ShieldCheck className="h-3.5 w-3.5 text-teal-600" />
                    <span>{sup.bank_name}: {sup.bank_account}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-[11px] text-amber-600">
                    <Lock className="h-3 w-3" />
                    <span>Datos bancarios restringidos</span>
                  </div>
                )}
              </td>
              <td className="px-4 py-3 text-right">{onQualification && <button type="button" onClick={() => onQualification(sup.id)} className="mr-2 rounded-lg border px-2.5 py-1 text-[11px]">Homologación</button>}
                <button
                  onClick={() => handleViewPerformance(sup.id)}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                >
                  Ver Desempeño
                </button>
              </td>
            </tr>
          ))}
          {filteredSuppliers.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-slate-400">No se encontraron proveedores registrados.</td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </section>);
}
