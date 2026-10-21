import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { ClipboardCheck as ActionClipboardCheck, CheckCheck as ActionCheckCheck } from "lucide-react";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Plus } from "lucide-react";
import { Submodule } from "../../types/InventoryWorkspaceTab";
import { TransferItem } from "../../types/InventoryWorkspaceTab";
import { CountItem } from "../../types/InventoryWorkspaceTab";

export function SeccionCounts({ canWrite, setModalType, counts, warehouses, setActiveCount, handleApproveCount }: { setModalType: ReturnType<typeof useInventoryWorkspaceTab>["setModalType"]; counts: ReturnType<typeof useInventoryWorkspaceTab>["counts"]; warehouses: ReturnType<typeof useInventoryWorkspaceTab>["warehouses"]; setActiveCount: ReturnType<typeof useInventoryWorkspaceTab>["setActiveCount"]; handleApproveCount: ReturnType<typeof useInventoryWorkspaceTab>["handleApproveCount"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubmodule?: Submodule;
    initialTransfers?: TransferItem[];
    initialCounts?: CountItem[];
  }["canWrite"]
}) {
  return (<section id="scr-024-counts-tab" className="space-y-4">
    <div className="flex justify-between items-center">
      <p className="text-xs text-slate-500">Sesiones de conteo ciego con segregación de funciones para aprobación.</p>
      {canWrite && (
        <button
          onClick={() => setModalType("create_count")}
          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Iniciar Conteo Ciego
        </button>
      )}
    </div>

    <div className="pagination-shell">
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">ID Conteo</th>
              <th className="px-4 py-3">Almacén</th>
              <th className="px-4 py-3">Fecha de Corte</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Líneas Contadas</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {counts.map(cnt => {
              const wh = warehouses.find(w => w.warehouse_id === cnt.warehouse_id)?.name || cnt.warehouse_id.substring(0, 8);
              return (
                <tr key={cnt.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-mono font-semibold text-slate-900">{cnt.count_code || "Conteo registrado"}</td>
                  <td className="px-4 py-3">{wh}</td>
                  <td className="px-4 py-3 text-slate-600">{cnt.cutoff_at.replace("T", " ").substring(0, 19)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ${cnt.status.toLowerCase() === "approved" ? "bg-teal-100 text-teal-800" :
                      cnt.status.toLowerCase() === "in_progress" ? "bg-amber-100 text-amber-800" :
                        "bg-slate-100 text-slate-700"
                      }`}>
                      {cnt.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{cnt.lines.filter(line => line.counted_at).length}/{cnt.lines.length} productos contados</td>
                  <td className="px-4 py-3 text-right">
                    <IconAction label={["in_progress", "pending_count"].includes(cnt.status.toLowerCase()) && canWrite ? "Registrar conteo" : "Revisar diferencias"} tone="neutral" onClick={() => setActiveCount(cnt)}><ActionClipboardCheck aria-hidden="true" /></IconAction>
                    {cnt.status.toLowerCase() === "pending_approval" && canWrite && (
                      <IconAction label="Aprobar y Ajustar" tone="primary" onClick={() => handleApproveCount(cnt.id)}><ActionCheckCheck aria-hidden="true" /></IconAction>
                    )}
                  </td>
                </tr>
              );
            })}
            {counts.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-400">Sin sesiones de conteo registradas.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>
  </section>);
}
