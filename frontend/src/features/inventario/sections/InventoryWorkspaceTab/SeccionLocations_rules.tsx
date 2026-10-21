import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { Pencil as ActionPencil, Power as ActionPower } from "lucide-react";
import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Submodule } from "../../types/InventoryWorkspaceTab";
import { TransferItem } from "../../types/InventoryWorkspaceTab";
import { CountItem } from "../../types/InventoryWorkspaceTab";

export function SeccionLocations_rules({ canWrite, setOperation, selectedWarehouseId, locations, warehouseName, rules, productName, deactivateRule }: { setOperation: ReturnType<typeof useInventoryWorkspaceTab>["setOperation"]; selectedWarehouseId: ReturnType<typeof useInventoryWorkspaceTab>["selectedWarehouseId"]; locations: ReturnType<typeof useInventoryWorkspaceTab>["locations"]; warehouseName: ReturnType<typeof useInventoryWorkspaceTab>["warehouseName"]; rules: ReturnType<typeof useInventoryWorkspaceTab>["rules"]; productName: ReturnType<typeof useInventoryWorkspaceTab>["productName"]; deactivateRule: ReturnType<typeof useInventoryWorkspaceTab>["deactivateRule"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubmodule?: Submodule;
    initialTransfers?: TransferItem[];
    initialCounts?: CountItem[];
  }["canWrite"]
}) {
  return (<section className="space-y-6">
    <article className="space-y-3">
      <div className="flex justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900">Ubicaciones Físicas Internas</h3>{canWrite && <button type="button" onClick={() => setOperation({ kind: "location", warehouse_id: selectedWarehouseId || undefined })} className="text-xs font-bold text-teal-700">Crear ubicación</button>}</div>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Pasillo</th>
              <th className="px-4 py-3">Estante / Rack</th>
              <th className="px-4 py-3">Nivel / Shelf</th>
              <th className="px-4 py-3">Bin</th>
              <th className="px-4 py-3 text-right">Capacidad Máxima</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {locations.map(loc => (
              <tr key={loc.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-medium text-slate-900">{loc.code} · {loc.aisle}<span className="block text-[10px] text-slate-500">{warehouseName(loc.warehouse_id)} · {loc.is_active ? "Activa" : "Inactiva"}</span>{canWrite && <IconAction label="Editar ubicación" tone="primary" onClick={() => setOperation({ kind: "location", id: loc.id, warehouse_id: loc.warehouse_id, values: { code: loc.code, aisle: loc.aisle, rack: loc.rack, shelf: loc.shelf, bin: loc.bin, capacity_units: loc.capacity_units, is_active: loc.is_active } })}><ActionPencil aria-hidden="true" /></IconAction>}</td>
                <td className="px-4 py-3">{loc.rack}</td>
                <td className="px-4 py-3">{loc.shelf}</td>
                <td className="px-4 py-3 font-mono">{loc.bin}</td>
                <td className="px-4 py-3 text-right tabular-nums">{loc.capacity_units ? Number(loc.capacity_units).toLocaleString("es-PE") : "Sin configurar"}</td>
              </tr>
            ))}
            {locations.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-400">Sin ubicaciones internas registradas.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </article>

    <article className="space-y-3">
      <div className="flex justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900">Reglas de Reposición y Stock Mínimo</h3>{canWrite && <button type="button" onClick={() => setOperation({ kind: "rule", warehouse_id: selectedWarehouseId || undefined })} className="text-xs font-bold text-teal-700">Crear regla</button>}</div>
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Producto / SKU</th>
              <th className="px-4 py-3 text-right">Stock Mínimo</th>
              <th className="px-4 py-3 text-right">Punto de Pedido</th>
              <th className="px-4 py-3 text-right">Cantidad de Reorden</th>
              <th className="px-4 py-3 text-right">Stock Máximo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rules.filter(rule => !selectedWarehouseId || rule.warehouse_id === selectedWarehouseId).map(r => (
              <tr key={r.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-mono text-slate-800">{productName(r.product_id)} · {warehouseName(r.warehouse_id)}<span className="block text-[10px]">{r.is_active === false ? "Inactiva" : "Activa"}</span>{canWrite && <div className="mt-1 flex gap-2"><IconAction label={r.is_active === false ? "Reactivar" : "Editar"} tone="primary" onClick={() => setOperation({ kind: "rule", product_id: r.product_id, warehouse_id: r.warehouse_id, values: { min_quantity: r.min_quantity, max_quantity: r.max_quantity, reorder_point: r.reorder_point, reorder_quantity: r.reorder_quantity } })}><ActionPower aria-hidden="true" /></IconAction>{r.is_active !== false && <IconAction label="Desactivar" tone="danger" onClick={() => deactivateRule(r.id)}><ActionPower aria-hidden="true" /></IconAction>}</div>}</td>
                <td className="px-4 py-3 text-right tabular-nums font-semibold text-amber-700">{Number(r.min_quantity).toFixed(0)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-700">{Number(r.reorder_point).toFixed(0)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-teal-700">{Number(r.reorder_quantity).toFixed(0)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-slate-500">{Number(r.max_quantity).toFixed(0)}</td>
              </tr>
            ))}
            {rules.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-400">Sin reglas de reposición configuradas.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </article>
  </section>);
}
