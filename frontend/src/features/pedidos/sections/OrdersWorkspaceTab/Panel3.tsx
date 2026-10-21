import type { useOrdersWorkspaceTab } from "../../hooks/useOrdersWorkspaceTab";


export function Panel3({ orders, setSelectedOrder }: { orders: ReturnType<typeof useOrdersWorkspaceTab>["orders"]; setSelectedOrder: ReturnType<typeof useOrdersWorkspaceTab>["setSelectedOrder"] }) {
  return (<div className="grid md:grid-cols-3 gap-4">
    {["draft", "confirmed", "fulfilled"].map(statusCol => {
      const colOrders = orders.filter(o => o.status === statusCol || (statusCol === "confirmed" && o.status === "partially_fulfilled"));
      const titles: Record<string, string> = {
        draft: "Borradores / Por Reservar",
        confirmed: "Confirmados / En Preparación",
        fulfilled: "Completados / Servidos"
      };
      return (
        <div key={statusCol} className="rounded-3xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">{titles[statusCol]}</h3>
            <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-700">{colOrders.length}</span>
          </div>
          <div className="space-y-2 max-h-[60vh] overflow-y-auto">
            {colOrders.map(o => (
              <div key={o.id} className="rounded-2xl border border-slate-200 bg-white p-3 shadow-xs space-y-2 text-xs">
                <div className="flex justify-between font-bold text-slate-900">
                  <span>{o.order_number}</span>
                  <span>${Number(o.total_amount).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <p className="text-[11px] text-slate-500 truncate">{o.customer_name || o.customer_id.substring(0, 8)}</p>
                <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px]">
                  <span className="text-slate-400">{o.status}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedOrder(o)}
                    className="font-bold text-teal-700 hover:underline"
                  >
                    Ver líneas
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    })}
  </div>);
}
