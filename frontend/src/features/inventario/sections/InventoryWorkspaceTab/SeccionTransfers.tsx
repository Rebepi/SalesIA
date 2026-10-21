import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { Send as ActionSend, PackageCheck as ActionPackageCheck } from "lucide-react";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Plus } from "lucide-react";
import { Submodule } from "../../types/InventoryWorkspaceTab";
import { TransferItem } from "../../types/InventoryWorkspaceTab";
import { CountItem } from "../../types/InventoryWorkspaceTab";

export function SeccionTransfers({ canWrite, setModalType, transfers, warehouses, handleDispatchTransfer, setActiveTransfer }: { setModalType: ReturnType<typeof useInventoryWorkspaceTab>["setModalType"]; transfers: ReturnType<typeof useInventoryWorkspaceTab>["transfers"]; warehouses: ReturnType<typeof useInventoryWorkspaceTab>["warehouses"]; handleDispatchTransfer: ReturnType<typeof useInventoryWorkspaceTab>["handleDispatchTransfer"]; setActiveTransfer: ReturnType<typeof useInventoryWorkspaceTab>["setActiveTransfer"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubmodule?: Submodule;
    initialTransfers?: TransferItem[];
    initialCounts?: CountItem[];
  }["canWrite"]
}) {
  return (<section id="scr-023-transfers-tab" className="space-y-4">
    <div className="flex justify-between items-center">
      <p className="text-xs text-slate-500">Transferencias intersucursales con conservación de stock en tránsito.</p>
      {canWrite && (
        <button
          onClick={() => setModalType("create_transfer")}
          className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Nueva Transferencia
        </button>
      )}
    </div>

    <div className="pagination-shell">
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Documento</th>
              <th className="px-4 py-3">Origen</th>
              <th className="px-4 py-3">Destino</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Líneas</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transfers.map(trf => {
              const src = warehouses.find(w => w.warehouse_id === trf.source_warehouse_id)?.name || trf.source_warehouse_id.substring(0, 8);
              const dst = warehouses.find(w => w.warehouse_id === trf.destination_warehouse_id)?.name || trf.destination_warehouse_id.substring(0, 8);
              return (
                <tr key={trf.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-mono font-semibold text-slate-900">{trf.document_number}</td>
                  <td className="px-4 py-3">{src}</td>
                  <td className="px-4 py-3">{dst}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ${trf.status === "received" ? "bg-teal-100 text-teal-800" :
                      trf.status === "in_transit" ? "bg-blue-100 text-blue-800" :
                        trf.status === "partially_received" ? "bg-amber-100 text-amber-800" :
                          "bg-slate-100 text-slate-700"
                      }`}>
                      {trf.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {trf.lines.map((l, idx) => (
                      <span key={idx} className="block text-[11px] text-slate-600">
                        {Number(l.quantity).toFixed(0)} u. (Recibidas: {Number(l.processed_quantity).toFixed(0)}, Dañadas: {Number(l.damaged_quantity).toFixed(0)})
                      </span>
                    ))}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1.5">
                      {trf.status === "draft" && canWrite && (
                        <IconAction label="Despachar" tone="neutral" onClick={() => handleDispatchTransfer(trf.id)}><ActionSend aria-hidden="true" /></IconAction>
                      )}
                      {(trf.status === "in_transit" || trf.status === "partially_received") && canWrite && (
                        <IconAction label="Recibir" tone="primary" onClick={() => { setActiveTransfer(trf); setModalType("receive_transfer"); }}><ActionPackageCheck aria-hidden="true" /></IconAction>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {transfers.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-400">Sin transferencias registradas.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>
  </section>);
}
