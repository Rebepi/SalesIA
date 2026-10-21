import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { SupplierCorrectivePanel } from "../../components/SupplierCorrectivePanel";
import { X } from "lucide-react";

export function SeccionSupplier_performance({ activePerformance, setModalType, canWrite = false, onReload }: { canWrite?: boolean; onReload?: () => void; activePerformance: NonNullable<ReturnType<typeof usePurchasesWorkspaceTab>["activePerformance"]>; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel max-h-[90vh] overflow-y-auto w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-bold text-slate-900">Desempeño: {activePerformance.legal_name}</h3>
          <p className="text-[11px] text-slate-500">Muestra auditada: {activePerformance.sample_size} líneas de recepción</p>
        </div>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      {activePerformance.warning && <p className="mt-3 text-xs text-amber-800">{activePerformance.warning}</p>}<p className="mt-3 text-sm">Puntuación ponderada: {activePerformance.weighted_score ?? "Sin muestra suficiente"} · Facturación conforme: {activePerformance.invoice_conformity_rate ?? "Sin datos"}</p>
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center">
          <p className="text-[11px] text-slate-500">Entregas a Tiempo (OTD)</p>
          <p className="mt-1 text-lg font-bold tabular-nums text-teal-700">{activePerformance.on_time_delivery_rate === null ? "Sin datos" : `${activePerformance.on_time_delivery_rate}%`}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center">
          <p className="text-[11px] text-slate-500">Tasa Cumplimiento (Fill Rate)</p>
          <p className="mt-1 text-lg font-bold tabular-nums text-blue-700">{activePerformance.fill_rate === null ? "Sin datos" : `${activePerformance.fill_rate}%`}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center">
          <p className="text-[11px] text-slate-500">Calidad Conforme</p>
          <p className="mt-1 text-lg font-bold tabular-nums text-purple-700">{activePerformance.quality_rate === null ? "Sin datos" : `${activePerformance.quality_rate}%`}</p>
        </div>
      </div>
      <div className="mt-4 max-h-48 text-[11px] pagination-shell">
        <PaginatedTable className="w-full text-left">
          <thead className="bg-slate-50 uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Recepción</th>
              <th className="px-3 py-2">Prometida</th>
              <th className="px-3 py-2">Real</th>
              <th className="px-3 py-2 text-right">A Tiempo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {activePerformance.sample_records.map(r => (
              <tr key={`${r.receipt_id}:${r.product_id || ""}`}>
                <td className="px-3 py-1.5 font-mono text-[10px] text-slate-500">{r.receipt_id.slice(0, 8)}</td>
                <td className="px-3 py-1.5">{r.promised_date ? new Date(r.promised_date).toLocaleDateString() : "Sin fecha prometida"}</td>
                <td className="px-3 py-1.5">{new Date(r.actual_date).toLocaleDateString()}</td>
                <td className="px-3 py-1.5 text-right font-semibold">
                  {r.is_on_time === null ? <span className="text-slate-500">Sin datos</span> : r.is_on_time ? <span className="text-teal-700">Sí</span> : <span className="text-red-700">Atrasado</span>}
                </td>
              </tr>
            ))}
            {activePerformance.sample_records.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-slate-400">Sin historial de recepciones con fecha prometida.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
      <SupplierCorrectivePanel supplierId={activePerformance.supplier_id} tasks={activePerformance.corrective_tasks || []} canWrite={canWrite} onChanged={() => onReload?.()} />
      <div className="flex justify-end pt-4">
        <button onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cerrar</button>
      </div>
    </div>
  </div>);
}
