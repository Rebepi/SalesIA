import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { apiClient } from "../../../../api/client";
import { PurchaseOrder } from "../../types/PurchasesWorkspaceTab";

export function SeccionRequisitions({ onCompareOffers, requisitions, canWrite, setEditorMode, setEditorSource, setModalType, toast, setRevision }: { onCompareOffers?: (id: string) => void; requisitions: ReturnType<typeof usePurchasesWorkspaceTab>["requisitions"]; setEditorMode: ReturnType<typeof usePurchasesWorkspaceTab>["setEditorMode"]; setEditorSource: ReturnType<typeof usePurchasesWorkspaceTab>["setEditorSource"]; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"]; toast: ReturnType<typeof usePurchasesWorkspaceTab>["toast"]; setRevision: ReturnType<typeof usePurchasesWorkspaceTab>["setRevision"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
    initialModalType?: string | null;
    initialActiveOrder?: PurchaseOrder | null;
  }["canWrite"]
}) {
  return (<section className="space-y-4">
    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Nº Requerimiento</th>
            <th className="px-4 py-3">Fecha Solicitud</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3">Líneas</th>
            <th className="px-4 py-3 text-right">Acción</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {requisitions.map(req => (
            <tr key={req.id} className="hover:bg-slate-50/60">
              <td className="px-4 py-3 font-semibold text-slate-900">#{req.document_number}</td>
              <td className="px-4 py-3 text-slate-500">{new Date(req.created_at).toLocaleDateString()}</td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                  {req.status}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-600">{req.lines.length} ítem(s)</td>
              <td className="px-4 py-3 text-right">
                {onCompareOffers && <button type="button" onClick={() => onCompareOffers(req.id)} className="mr-2 rounded-lg border px-3 py-2 text-xs">Comparar ofertas</button>}
                {req.status === "approved" && canWrite && <button type="button" onClick={() => { setEditorMode("order"); setEditorSource({ id: req.id, version: req.version, warehouse_id: req.warehouse_id, supplier_id: req.details?.suggested_supplier_id, lines: req.lines }); setModalType("create_order"); }} className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-semibold text-white">Convertir en orden</button>}
                {req.status === "converted" && <span className="text-xs text-teal-700">Orden generada · referencia conservada</span>}
                {req.status === "pending_approval" && canWrite && (
                  <button
                    onClick={async () => {
                      try {
                        await apiClient.request(`/api/v1/purchases/requisitions/${req.id}/approve`, { method: "POST" });
                        toast.success("Aprobado", "Requerimiento interno autorizado.");
                        setRevision(r => r + 1);
                      } catch (err: unknown) {
                        const msg = typeof err === "object" && err !== null && "detail" in err ? String(err.detail) : "Error al autorizar";
                        toast.error("Error", msg);
                      }
                    }}
                    className="rounded-lg bg-teal-700 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-teal-800"
                  >
                    Aprobar
                  </button>
                )}
              </td>
            </tr>
          ))}
          {requisitions.length === 0 && (
            <tr>
              <td colSpan={5} className="py-8 text-center text-slate-400">No hay solicitudes internas registradas.</td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </section>);
}
