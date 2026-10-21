import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { History as ActionHistory, Lock as ActionLock } from "lucide-react";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { inventoryTrackingStatus } from "../../components/InventoryTraceDialog";
import { Submodule } from "../../types/InventoryWorkspaceTab";
import { TransferItem } from "../../types/InventoryWorkspaceTab";
import { CountItem } from "../../types/InventoryWorkspaceTab";

export function SeccionLots_serials({ canWrite, setOperation, lots, search, productName, blockLot, setTrace, selectedWarehouseId, serials, warehouseName }: { setOperation: ReturnType<typeof useInventoryWorkspaceTab>["setOperation"]; lots: ReturnType<typeof useInventoryWorkspaceTab>["lots"]; search: ReturnType<typeof useInventoryWorkspaceTab>["search"]; productName: ReturnType<typeof useInventoryWorkspaceTab>["productName"]; blockLot: ReturnType<typeof useInventoryWorkspaceTab>["blockLot"]; setTrace: ReturnType<typeof useInventoryWorkspaceTab>["setTrace"]; selectedWarehouseId: ReturnType<typeof useInventoryWorkspaceTab>["selectedWarehouseId"]; serials: ReturnType<typeof useInventoryWorkspaceTab>["serials"]; warehouseName: ReturnType<typeof useInventoryWorkspaceTab>["warehouseName"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubmodule?: Submodule;
    initialTransfers?: TransferItem[];
    initialCounts?: CountItem[];
  }["canWrite"]
}) {
  return (<section className="space-y-6">
    <article className="space-y-3">
      <div className="flex justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900">Control de Lotes y Caducidades</h3>{canWrite && <button type="button" onClick={() => setOperation({ kind: "lot" })} className="text-xs font-bold text-teal-700">Registrar lote</button>}</div>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Código de Lote</th>
              <th className="px-4 py-3">Producto / SKU</th>
              <th className="px-4 py-3">Fecha de Vencimiento</th>
              <th className="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {lots.filter(lot => !search || productName(lot.product_id).toLowerCase().includes(search.toLowerCase()) || lot.lot_code.toLowerCase().includes(search.toLowerCase())).map(lot => (
              <tr key={lot.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-mono font-semibold text-slate-900">{lot.lot_code}</td>
                <td className="px-4 py-3 font-mono text-[10px] text-slate-500">{productName(lot.product_id)}</td>
                <td className="px-4 py-3 text-slate-600">{lot.expiration_date ? lot.expiration_date.substring(0, 10) : "Sin vencimiento"}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${lot.is_blocked ? "bg-red-100 text-red-800" : "bg-teal-100 text-teal-800"}`}>
                    {lot.is_blocked ? "BLOQUEADO" : "ACTIVO"}{canWrite && !lot.is_blocked && <IconAction label="Bloquear lote" tone="danger" onClick={() => blockLot(lot.id)}><ActionLock aria-hidden="true" /></IconAction>}
                  </span>
                  <IconAction label="Ver trazabilidad" tone="neutral" onClick={() => setTrace({ kind: "lot", id: lot.id })}><ActionHistory aria-hidden="true" /></IconAction>
                </td>
              </tr>
            ))}
            {lots.length === 0 && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-slate-400">Sin lotes registrados.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </article>

    <article className="space-y-3">
      <div className="flex justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900">Series Únicas Rastreadas</h3>{canWrite && <button type="button" onClick={() => setOperation({ kind: "serial", warehouse_id: selectedWarehouseId || undefined })} className="text-xs font-bold text-teal-700">Registrar serie</button>}</div>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Número de Serie</th>
              <th className="px-4 py-3">Almacén</th>
              <th className="px-4 py-3">Producto</th>
              <th className="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {serials.filter(item => (!selectedWarehouseId || item.warehouse_id === selectedWarehouseId) && (!search || productName(item.product_id).toLowerCase().includes(search.toLowerCase()) || item.serial_number.toLowerCase().includes(search.toLowerCase()))).map(s => (
              <tr key={s.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-mono font-semibold text-slate-900">{s.serial_number}</td>
                <td className="px-4 py-3 text-slate-600">{warehouseName(s.warehouse_id)}</td>
                <td className="px-4 py-3 text-slate-600">{productName(s.product_id)}</td>
                <td className="px-4 py-3">
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-800">{inventoryTrackingStatus(s.status)}</span><IconAction label="Ver trazabilidad" tone="neutral" onClick={() => setTrace({ kind: "serial", id: s.id })}><ActionHistory aria-hidden="true" /></IconAction>
                </td>
              </tr>
            ))}
            {serials.length === 0 && (
              <tr>
                <td colSpan={4} className="p-6 text-center text-slate-400">Sin números de serie registrados.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </article>
  </section>);
}
