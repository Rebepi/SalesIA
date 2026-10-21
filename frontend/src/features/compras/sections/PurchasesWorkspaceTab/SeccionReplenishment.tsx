import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { AlertTriangle, CheckCircle2, ShoppingBag } from "lucide-react";
import { PurchaseOrder } from "../../types/PurchasesWorkspaceTab";

export function SeccionReplenishment({ replenishmentWarehouse, setReplenishmentWarehouse, setSelectedSuggestions, warehouses, canWrite, selectedSuggestions, prepareSuggestions, suggestions }: { replenishmentWarehouse: ReturnType<typeof usePurchasesWorkspaceTab>["replenishmentWarehouse"]; setReplenishmentWarehouse: ReturnType<typeof usePurchasesWorkspaceTab>["setReplenishmentWarehouse"]; setSelectedSuggestions: ReturnType<typeof usePurchasesWorkspaceTab>["setSelectedSuggestions"]; warehouses: ReturnType<typeof usePurchasesWorkspaceTab>["warehouses"]; selectedSuggestions: ReturnType<typeof usePurchasesWorkspaceTab>["selectedSuggestions"]; prepareSuggestions: ReturnType<typeof usePurchasesWorkspaceTab>["prepareSuggestions"]; suggestions: ReturnType<typeof usePurchasesWorkspaceTab>["suggestions"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
    initialModalType?: string | null;
    initialActiveOrder?: PurchaseOrder | null;
  }["canWrite"]
}) {
  return (<section className="space-y-4">
    <div className="flex flex-wrap items-end gap-3"><label className="text-xs font-semibold">Almacén para reposición<CustomSelect remote={{ resource: "warehouses" }} value={replenishmentWarehouse} onChange={event => { setReplenishmentWarehouse(event.target.value); setSelectedSuggestions([]); }} className="mt-1 min-w-56"><option value="">Todos (elige uno para crear documentos)</option>{warehouses.map(item => <option key={item.warehouse_id} value={item.warehouse_id}>{item.name} ({item.code})</option>)}</CustomSelect></label>{canWrite && <><button disabled={!replenishmentWarehouse || !selectedSuggestions.length} onClick={() => prepareSuggestions("requisition")} className="rounded-xl bg-teal-700 px-3 py-2 text-xs text-white disabled:opacity-50">Crear requisición ({selectedSuggestions.length})</button><button disabled={!replenishmentWarehouse || !selectedSuggestions.length} onClick={() => prepareSuggestions("order")} className="rounded-xl border px-3 py-2 text-xs disabled:opacity-50">Preparar orden de compra</button></>}</div>
    <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-4 text-xs text-blue-900">
      <h4 className="font-bold flex items-center gap-1.5">
        <ShoppingBag className="h-4 w-4 text-blue-700" />
        Motor de Cálculo de Sugerencias de Reposición
      </h4>
      <p className="mt-1 text-blue-800">
        Las propuestas usan la historia configurada, el plazo vigente del proveedor y las reglas de stock. Las compras aprobadas pendientes reducen el faltante; se muestran los retrasos para revisarlos antes de comprar nuevamente.
      </p>
    </div>

    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Selección</th><th className="px-4 py-3">Producto / SKU</th>
            <th className="px-4 py-3 text-right">Disponible</th>
            <th className="px-4 py-3 text-right">Demanda Diaria</th>
            <th className="px-4 py-3 text-right">Lead Time</th>
            <th className="px-4 py-3 text-right">Stock Seguridad</th>
            <th className="px-4 py-3 text-right">Sugerencia</th>
            <th className="px-4 py-3">Estado Algoritmo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {suggestions.map(s => (
            <tr key={s.product_id} className="hover:bg-slate-50/60"><td className="px-4 py-3"><input type="checkbox" aria-label={`Seleccionar ${s.sku}`} disabled={!canWrite || !replenishmentWarehouse || Number(s.suggested_quantity) <= 0} checked={selectedSuggestions.includes(s.product_id)} onChange={event => setSelectedSuggestions(previous => event.target.checked ? [...previous, s.product_id] : previous.filter(id => id !== s.product_id))} /></td>
              <td className="px-4 py-3 font-medium text-slate-900">
                <div>{s.product_name}</div>{s.warnings?.map(warning => <p key={warning} className="mt-1 max-w-xs text-[10px] text-amber-800">{warning}</p>)}
                <span className="font-mono text-[10px] text-slate-400">{s.sku}</span>
              </td>
              <td className="px-4 py-3 text-right tabular-nums">{Number(s.current_available).toFixed(2)}<span className="block text-[10px] text-slate-500">Compras pendientes: {s.pending_purchase_quantity || "0"} · Tránsito: {s.in_transit_quantity || "0"}</span><span className="block text-[10px] text-slate-500">Posición: {s.inventory_position || s.current_available}</span></td>
              <td className="px-4 py-3 text-right tabular-nums">{Number(s.assumptions.daily_demand).toFixed(2)} /día</td>
              <td className="px-4 py-3 text-right tabular-nums">{s.assumptions.lead_time_days} días<span className="block text-[10px] text-slate-500">{s.currency}</span></td>
              <td className="px-4 py-3 text-right tabular-nums">{Number(s.assumptions.safety_stock).toFixed(2)}</td>
              <td className="px-4 py-3 text-right font-bold tabular-nums text-teal-700">
                {Number(s.suggested_quantity).toFixed(2)} un.
              </td>
              <td className="px-4 py-3">
                {s.data_insufficient || s.status === "NEEDS_REVIEW" ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
                    <AlertTriangle className="h-3 w-3" />
                    Datos insuficientes (Revisión manual)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                    <CheckCircle2 className="h-3 w-3" />
                    Listo para requerimiento
                  </span>
                )}
              </td>
            </tr>
          ))}
          {suggestions.length === 0 && (
            <tr>
              <td colSpan={8} className="py-8 text-center text-slate-400">No hay productos candidatos a reposición en este momento.</td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </section>);
}
