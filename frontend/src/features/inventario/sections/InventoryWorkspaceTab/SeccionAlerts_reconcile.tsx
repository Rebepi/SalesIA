import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { PackageCheck as ActionPackageCheck, Trash2 as ActionTrash2 } from "lucide-react";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { AlertTriangle, RefreshCw, Wrench } from "lucide-react";

export function SeccionAlerts_reconcile({ handleRecalculateAlerts, setModalType, alerts, quarantineItems, productName, warehouseName, handleClassifyQuarantine }: { handleRecalculateAlerts: ReturnType<typeof useInventoryWorkspaceTab>["handleRecalculateAlerts"]; setModalType: ReturnType<typeof useInventoryWorkspaceTab>["setModalType"]; alerts: ReturnType<typeof useInventoryWorkspaceTab>["alerts"]; quarantineItems: ReturnType<typeof useInventoryWorkspaceTab>["quarantineItems"]; productName: ReturnType<typeof useInventoryWorkspaceTab>["productName"]; warehouseName: ReturnType<typeof useInventoryWorkspaceTab>["warehouseName"]; handleClassifyQuarantine: ReturnType<typeof useInventoryWorkspaceTab>["handleClassifyQuarantine"] }) {
  return (<section className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-xs text-slate-500">Alertas operativas deduplicadas y auditoría de libro mayor contra saldos físicos.</p>
      <div className="flex gap-2">
        <button
          onClick={handleRecalculateAlerts}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Recalcular Alertas
        </button>
        <button
          onClick={() => setModalType("reconcile")}
          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3 py-2 text-xs font-semibold text-white hover:bg-teal-800"
        >
          <Wrench className="h-3.5 w-3.5" />
          Auditar Saldo vs Kardex
        </button>
      </div>
    </div>

    <article className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-900">Alertas Activas del Sistema</h3>
      <div className="space-y-2">
        {alerts.map(a => (
          <div key={a.id} className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/60 p-4">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 text-xs">{a.alert_type}</span>
                <span className="rounded bg-amber-200/70 px-1.5 py-0.2 text-[9px] font-bold text-amber-900">{a.severity}</span>
              </div>
              <p className="mt-0.5 text-xs text-slate-700">{a.message}</p>
              <span className="mt-1 block text-[10px] text-slate-400">Calculada el {a.computed_at.replace("T", " ").substring(0, 19)}</span>
            </div>
          </div>
        ))}
        {alerts.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-xs text-slate-400">
            No hay alertas activas en el inventario.
          </div>
        )}
      </div>
    </article>

    <article className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-900">Mercadería en Cuarentena</h3>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Motivo</th>
              <th className="px-4 py-3">Producto / SKU</th>
              <th className="px-4 py-3 text-right">Cantidad</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3 text-right">Acción Técnica</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {quarantineItems.map(q => (
              <tr key={q.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-medium text-slate-900">{q.reason}</td>
                <td className="px-4 py-3 font-mono text-slate-500">{productName(q.product_id)} · {warehouseName(q.warehouse_id)}</td>
                <td className="px-4 py-3 text-right tabular-nums font-semibold text-red-700">{Number(q.quantity).toFixed(2)}</td>
                <td className="px-4 py-3">
                  <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-800">{q.status}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-1.5">
                    <IconAction label="Reintegrar a Stock" tone="primary" onClick={() => handleClassifyQuarantine(q.id, "RESTOCK")}><ActionPackageCheck aria-hidden="true" /></IconAction>
                    <IconAction label="Desechar Merma" tone="danger" onClick={() => handleClassifyQuarantine(q.id, "SCRAP")}><ActionTrash2 aria-hidden="true" /></IconAction>
                  </div>
                </td>
              </tr>
            ))}
            {quarantineItems.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-400">Sin unidades retenidas en cuarentena.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </article>
  </section>);
}
