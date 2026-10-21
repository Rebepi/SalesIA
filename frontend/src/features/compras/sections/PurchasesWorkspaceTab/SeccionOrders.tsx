import { useState } from "react";
import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { PurchaseOrder } from "../../types/PurchasesWorkspaceTab";
import { MoreHorizontal, BarChart2, PackageCheck, CheckCircle, RotateCcw, GitMerge } from "lucide-react";

export function SeccionOrders({ orders, handleViewTimeline, setActiveOrder, setModalType, canWrite, handleApproveOrder }: { orders: ReturnType<typeof usePurchasesWorkspaceTab>["orders"]; handleViewTimeline: ReturnType<typeof usePurchasesWorkspaceTab>["handleViewTimeline"]; setActiveOrder: ReturnType<typeof usePurchasesWorkspaceTab>["setActiveOrder"]; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"]; handleApproveOrder: ReturnType<typeof usePurchasesWorkspaceTab>["handleApproveOrder"] } & {
  canWrite: {
    canWrite: boolean;
    initialSubtab?: "suppliers" | "orders" | "requisitions" | "replenishment";
    initialModalType?: string | null;
    initialActiveOrder?: PurchaseOrder | null;
  }["canWrite"]
}) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  return (<section id="scr-026-purchases-tab" className="space-y-4">
    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="px-4 py-3">Nº Orden</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3">Versión</th>
            <th className="px-4 py-3">Líneas / Cantidad</th>
            <th className="px-4 py-3 text-right">Importe Total</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {orders.map(ord => {
            const total = ord.lines.reduce((acc, l) => acc + Number(l.quantity) * Number(l.unit_cost), 0);
            const menuOpen = openMenuId === ord.id;
            return (
              <tr key={ord.id} className="hover:bg-slate-50/60">
                <td className="px-4 py-3 font-semibold text-slate-900">
                  <div>#{ord.document_number}</div>
                  <span className="text-[10px] text-slate-400">{new Date(ord.created_at).toLocaleDateString()}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${ord.status === "approved" ? "bg-teal-100 text-teal-800" :
                    ord.status === "received" ? "bg-emerald-100 text-emerald-800" :
                      ord.status === "partially_received" ? "bg-blue-100 text-blue-800" :
                        ord.status === "cancelled" ? "bg-red-100 text-red-800" :
                          "bg-amber-100 text-amber-800"
                    }`}>
                    {ord.status}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-slate-600">v{ord.version}</td>
                <td className="px-4 py-3 text-slate-700">
                  {ord.lines.length} ítem(s) · {ord.lines.reduce((sum, line) => sum + Number(line.quantity), 0)} un.
                </td>
                <td className="px-4 py-3 text-right font-bold tabular-nums text-slate-900">
                  {ord.details?.currency || "USD"} {Number(ord.details?.total ?? total).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {ord.status === "submitted" && canWrite && (
                      <button
                        onClick={() => handleApproveOrder(ord.id)}
                        className="rounded-lg bg-teal-700 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-teal-800"
                      >
                        Aprobar
                      </button>
                    )}
                    {(ord.status === "approved" || ord.status === "partially_received") && canWrite && (
                      <button
                        onClick={() => { setActiveOrder(ord); setModalType("receive_goods"); }}
                        className="rounded-lg bg-blue-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-blue-700"
                      >
                        Recibir
                      </button>
                    )}
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setOpenMenuId(menuOpen ? null : ord.id)}
                        className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-500 hover:bg-slate-100"
                        title="Más opciones"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                      {menuOpen && (
                        <div
                          onMouseLeave={() => setOpenMenuId(null)}
                          className="absolute right-0 top-8 z-40 w-48 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900 text-left"
                        >
                          <button type="button" onClick={() => { setActiveOrder(ord); setModalType("order_control"); setOpenMenuId(null); }} className="flex w-full rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50">Revisión, saldos e historial</button>
                          <button
                            type="button"
                            onClick={() => { handleViewTimeline(ord.id); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                          >
                            <BarChart2 className="h-3.5 w-3.5" />
                            <span>Timeline</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => { setActiveOrder(ord); setModalType("receive_goods"); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                          >
                            <PackageCheck className="h-3.5 w-3.5" />
                            <span>Recepciones</span>
                          </button>
                          {(ord.status === "received" || ord.status === "partially_received") && canWrite && (
                            <>
                              <button
                                type="button"
                                onClick={() => { setActiveOrder(ord); setModalType("landed_cost"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-teal-700 hover:bg-teal-50"
                              >
                                <CheckCircle className="h-3.5 w-3.5" />
                                <span>Costos Prorr.</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => { setActiveOrder(ord); setModalType("purchase_return"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-red-700 hover:bg-red-50"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                <span>Devolución</span>
                              </button>
                            </>
                          )}
                          {ord.status !== "cancelled" && (
                            <button
                              type="button"
                              onClick={() => { setActiveOrder(ord); setModalType("three_way_match"); setOpenMenuId(null); }}
                              className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-purple-700 hover:bg-purple-50"
                            >
                              <GitMerge className="h-3.5 w-3.5" />
                              <span>3 Vías</span>
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            );
          })}
          {orders.length === 0 && (
            <tr>
              <td colSpan={6} className="py-8 text-center text-slate-400">No hay órdenes de compra registradas.</td>
            </tr>
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </section>);
}
