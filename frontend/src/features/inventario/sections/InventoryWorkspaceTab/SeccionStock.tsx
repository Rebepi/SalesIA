import { IconAction } from "../../../../ui/components/primitives/IconAction";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { History, Send, Wrench } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { Submodule } from "../../types/InventoryWorkspaceTab";
import { TransferItem } from "../../types/InventoryWorkspaceTab";
import { CountItem } from "../../types/InventoryWorkspaceTab";

export function SeccionStock({ totalAvailable, totalReserved, totalInTransit, totalQuarantine, filteredStock, productName, warehouseName, setProductFilter, setSubmodule, canWrite, setOperation, setTransferContext, setModalType }: { totalAvailable: ReturnType<typeof useInventoryWorkspaceTab>["totalAvailable"]; totalReserved: ReturnType<typeof useInventoryWorkspaceTab>["totalReserved"]; totalInTransit: ReturnType<typeof useInventoryWorkspaceTab>["totalInTransit"]; totalQuarantine: ReturnType<typeof useInventoryWorkspaceTab>["totalQuarantine"]; filteredStock: ReturnType<typeof useInventoryWorkspaceTab>["filteredStock"]; productName: ReturnType<typeof useInventoryWorkspaceTab>["productName"]; warehouseName: ReturnType<typeof useInventoryWorkspaceTab>["warehouseName"]; setProductFilter: ReturnType<typeof useInventoryWorkspaceTab>["setProductFilter"]; setSubmodule: ReturnType<typeof useInventoryWorkspaceTab>["setSubmodule"]; setOperation: ReturnType<typeof useInventoryWorkspaceTab>["setOperation"]; setTransferContext: ReturnType<typeof useInventoryWorkspaceTab>["setTransferContext"]; setModalType: ReturnType<typeof useInventoryWorkspaceTab>["setModalType"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubmodule?: Submodule;
    initialTransfers?: TransferItem[];
    initialCounts?: CountItem[];
  }["canWrite"]
}) {
  return (<section id="scr-021-inventory-stock" className="flex flex-col flex-1 min-h-0 gap-2.5 overflow-hidden">
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 flex-shrink-0">
      <div className="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 py-2.5">
        <p className="flex items-center gap-1 text-[11px] text-slate-500">Vendible Disponible <InfoTooltip title="Stock vendible" description="Unidades físicas libres de reservas, bloqueos, tránsito y cuarentena que pueden venderse ahora." /></p>
        <p className="mt-0.5 text-lg font-bold tabular-nums text-teal-700 dark:text-teal-400">{totalAvailable.toFixed(2)}</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 py-2.5">
        <p className="flex items-center gap-1 text-[11px] text-slate-500">Reservado por Ventas <InfoTooltip title="Stock reservado" description="Unidades apartadas para pedidos confirmados y todavía no despachadas." /></p>
        <p className="mt-0.5 text-lg font-bold tabular-nums text-amber-700 dark:text-amber-400">{totalReserved.toFixed(2)}</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 py-2.5">
        <p className="flex items-center gap-1 text-[11px] text-slate-500">En Tránsito Transferencias <InfoTooltip title="Stock en tránsito" description="Unidades enviadas entre almacenes que aún no han sido recibidas en destino." /></p>
        <p className="mt-0.5 text-lg font-bold tabular-nums text-blue-700 dark:text-blue-400">{totalInTransit.toFixed(2)}</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-900/80 px-3 py-2.5">
        <p className="flex items-center gap-1 text-[11px] text-slate-500">Retenido en Cuarentena <InfoTooltip align="right" title="Stock en cuarentena" description="Unidades retenidas por revisión de calidad y no disponibles para venta o despacho." /></p>
        <p className="mt-0.5 text-lg font-bold tabular-nums text-red-700 dark:text-red-400">{totalQuarantine.toFixed(2)}</p>
      </div>
    </div>

    <div className="pagination-shell flex-1 min-h-0 flex flex-col overflow-hidden">
      <div className="pagination-shell flex-1 min-h-0 flex flex-col overflow-hidden">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">SKU / Producto</th>
              <th className="px-4 py-3 text-right">Físico</th>
              <th className="px-4 py-3 text-right">Reservado</th>
              <th className="px-4 py-3 text-right">Disponible</th>
              <th className="px-4 py-3 text-right">En Tránsito</th>
              <th className="px-4 py-3 text-right">Cuarentena</th>
              <th className="px-4 py-3 text-right">Bloqueado</th>
              <th className="px-4 py-3 text-right">Costo Promedio</th><th className="px-4 py-3 w-px whitespace-nowrap">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredStock.map(item => (
              <tr key={item.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-medium text-slate-900">
                  <div>{item.product_name || productName(item.product_id)}</div>
                  <span className="font-mono text-[10px] text-slate-400">{item.sku} · {item.unit_of_measure} · {warehouseName(item.warehouse_id)}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">{Number(item.physical_quantity).toFixed(2)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-amber-600">{Number(item.reserved_quantity).toFixed(2)}</td>
                <td className="px-4 py-3 text-right tabular-nums font-semibold text-teal-700">{Number(item.available_quantity).toFixed(2)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-blue-600">{Number(item.transit_quantity).toFixed(2)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-red-600">{Number(item.quarantine_quantity).toFixed(2)}</td>
                <td className="px-4 py-3 text-right tabular-nums">{Number(item.average_cost).toFixed(4)}</td>
                <td className="px-4 py-3 w-px whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver Kardex" tone="neutral" onClick={() => { setProductFilter(item.product_id); setSubmodule("kardex"); }}><History className="h-4 w-4" /></IconAction>
                    {canWrite && (
                      <>
                        <IconAction className="!border-teal-200 !bg-teal-50 !text-teal-700 enabled:hover:!bg-teal-100 dark:!border-teal-700/60 dark:!bg-teal-500/15 dark:!text-teal-300 dark:enabled:hover:!bg-teal-500/25" label="Ajustar existencias" tone="neutral" onClick={() => setOperation({ kind: "adjustment", product_id: item.product_id, warehouse_id: item.warehouse_id, values: { unit_cost: item.average_cost } })}><Wrench className="h-4 w-4" /></IconAction>
                        <IconAction className="!border-violet-200 !bg-violet-50 !text-violet-700 enabled:hover:!bg-violet-100 dark:!border-violet-700/60 dark:!bg-violet-500/15 dark:!text-violet-300 dark:enabled:hover:!bg-violet-500/25" label="Transferir stock" tone="neutral" onClick={() => { setTransferContext({ sourceId: item.warehouse_id, productId: item.product_id }); setModalType("create_transfer"); }}><Send className="h-4 w-4" /></IconAction>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filteredStock.length === 0 && (
              <tr>
                <td colSpan={8} className="p-8 text-center text-slate-400">Sin existencias registradas para el filtro seleccionado.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>
  </section>);
}
