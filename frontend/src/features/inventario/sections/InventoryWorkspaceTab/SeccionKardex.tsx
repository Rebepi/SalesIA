import type { useInventoryWorkspaceTab } from "../../hooks/useInventoryWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";

export function SeccionKardex({ kardexItems }: { kardexItems: ReturnType<typeof useInventoryWorkspaceTab>["kardexItems"] }) {
  return (<section id="scr-022-kardex-tab" className="space-y-4">
    <div className="pagination-shell">
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-xs">
          <thead className="bg-slate-100 uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Fecha y Hora</th>
              <th className="px-4 py-3">Operación</th>
              <th className="px-4 py-3">Referencia</th>
              <th className="px-4 py-3 text-right">Variación</th>
              <th className="px-4 py-3 text-right">Saldo Físico</th>
              <th className="px-4 py-3 text-right">Costo Operación</th>
              <th className="px-4 py-3 text-right">Costo Promedio</th><th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {kardexItems.map(item => {
              const delta = Number(item.quantity_delta);
              return (
                <tr key={item.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-mono text-[11px] text-slate-600">{item.occurred_at.replace("T", " ").substring(0, 19)}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{item.movement_type}</td>
                  <td className="px-4 py-3 font-mono text-[10px] text-slate-500">{item.reference_doc_type} #{item.reference_doc_id.substring(0, 8)}</td>
                  <td className={`px-4 py-3 text-right tabular-nums font-semibold ${delta > 0 ? "text-teal-700" : "text-rose-700"}`}>
                    {delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums font-semibold">{Number(item.resulting_physical_qty).toFixed(2)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{Number(item.unit_cost).toFixed(4)}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-500">{Number(item.moving_average_cost).toFixed(4)}</td>
                </tr>
              );
            })}
            {kardexItems.length === 0 && (
              <tr>
                <td colSpan={7} className="p-8 text-center text-slate-400">Sin movimientos registrados en el kardex.</td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>
  </section>);
}
