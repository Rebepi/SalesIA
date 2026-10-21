import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { useState } from "react";
import type { useOrdersWorkspaceTab } from "../../hooks/useOrdersWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Eye, CheckCheck, Truck, ShieldCheck, PackageCheck, Copy, RotateCcw, Unlock, Ban, MoreHorizontal } from "lucide-react";

export function Panel2({ orders, canWrite, busy, handleConfirmAndReserve, orderAction, openFulfillModal, openShortages, setSelectedOrder }: { orders: ReturnType<typeof useOrdersWorkspaceTab>["orders"]; busy: ReturnType<typeof useOrdersWorkspaceTab>["busy"]; handleConfirmAndReserve: ReturnType<typeof useOrdersWorkspaceTab>["handleConfirmAndReserve"]; orderAction: ReturnType<typeof useOrdersWorkspaceTab>["orderAction"]; openFulfillModal: ReturnType<typeof useOrdersWorkspaceTab>["openFulfillModal"]; openShortages: ReturnType<typeof useOrdersWorkspaceTab>["openShortages"]; setSelectedOrder: ReturnType<typeof useOrdersWorkspaceTab>["setSelectedOrder"] } & { canWrite: NonNullable<{ canWrite?: boolean }["canWrite"]> }) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  return (<div className="pagination-shell">
    <div className="pagination-shell">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
          <tr>
            <th className="px-5 py-3.5">Número</th>
            <th className="px-5 py-3.5">Cliente</th>
            <th className="px-5 py-3.5">Total</th>
            <th className="px-5 py-3.5">Reserva de Stock</th>
            <th className="px-5 py-3.5">Estado</th>
            <th className="px-5 py-3.5 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {orders.length === 0 ? (
            <tr key="empty">
              <td colSpan={6} className="py-12 text-center text-slate-400">
                No hay pedidos registrados en este estado.
              </td>
            </tr>
          ) : (
            orders.map(o => {
              const menuOpen = openMenuId === (o.order_id ?? o.id ?? o.order_number);
              return (
                <tr key={o.order_id ?? o.id ?? o.order_number} className="hover:bg-slate-50/80 transition">
                  <td className="px-5 py-3.5 font-mono font-bold text-slate-900">{o.order_number}</td>
                  <td className="px-5 py-3.5 font-medium text-slate-800">{o.customer_name || o.customer_id.substring(0, 8)}</td>
                  <td className="px-5 py-3.5 font-black text-slate-900">${Number(o.total_amount).toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {o.currency}</td>
                  <td className="px-5 py-3.5">
                    {o.stock_reserved ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
                        <ShieldCheck className="h-3 w-3" /> Reservado
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400">Sin reserva</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase ${o.status === "fulfilled"
                      ? "bg-emerald-100 text-emerald-800"
                      : o.status === "partially_fulfilled"
                        ? "bg-amber-100 text-amber-800"
                        : o.status === "confirmed"
                          ? "bg-teal-100 text-teal-800"
                          : "bg-slate-100 text-slate-600"
                      }`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {canWrite && o.status === "draft" && (
                        <IconAction className="!border-teal-200 !bg-teal-50 !text-teal-700 enabled:hover:!bg-teal-100 dark:!border-teal-700/60 dark:!bg-teal-500/15 dark:!text-teal-300 dark:enabled:hover:!bg-teal-500/25" label="Reservar stock" tone="primary" disabled={busy} onClick={() => handleConfirmAndReserve(o)}><ShieldCheck aria-hidden="true" /></IconAction>
                      )}
                      {canWrite && o.status === "pending_approval" && (
                        <IconAction className="!border-violet-200 !bg-violet-50 !text-violet-700 enabled:hover:!bg-violet-100 dark:!border-violet-700/60 dark:!bg-violet-500/15 dark:!text-violet-300 dark:enabled:hover:!bg-violet-500/25" label="Aprobar pedido" tone="primary" disabled={busy} onClick={() => orderAction(o, "approve")}><CheckCheck aria-hidden="true" /></IconAction>
                      )}
                      {canWrite && (o.status === "confirmed" || o.status === "partially_fulfilled") && (
                        <IconAction className="!border-emerald-200 !bg-emerald-50 !text-emerald-700 enabled:hover:!bg-emerald-100 dark:!border-emerald-700/60 dark:!bg-emerald-500/15 dark:!text-emerald-300 dark:enabled:hover:!bg-emerald-500/25" label="Despachar pedido" tone="primary" disabled={busy} onClick={() => openFulfillModal(o)}><Truck aria-hidden="true" /></IconAction>
                      )}
                      <IconAction className="!border-sky-200 !bg-sky-50 !text-sky-700 enabled:hover:!bg-sky-100 dark:!border-sky-700/60 dark:!bg-sky-500/15 dark:!text-sky-300 dark:enabled:hover:!bg-sky-500/25" label="Ver detalle del pedido" tone="neutral" onClick={() => setSelectedOrder(o)}><Eye aria-hidden="true" /></IconAction>
                      <div className="relative">
                        <IconAction className="!border-slate-200 !bg-slate-50 !text-slate-700 enabled:hover:!bg-slate-100 dark:!border-slate-700/60 dark:!bg-slate-500/15 dark:!text-slate-300 dark:enabled:hover:!bg-slate-500/25" label="Más opciones" tone="neutral" aria-expanded={menuOpen} aria-haspopup="true" onClick={() => setOpenMenuId(menuOpen ? null : (o.order_id ?? o.id ?? o.order_number))}><MoreHorizontal aria-hidden="true" /></IconAction>
                        {menuOpen && (
                          <div
                            onMouseLeave={() => setOpenMenuId(null)}
                            className="absolute right-0 top-8 z-40 w-52 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900 text-left"
                          >
                            {canWrite && o.stock_reserved && (
                              <button
                                type="button"
                                title="Liberar reserva"
                                disabled={busy}
                                onClick={() => { orderAction(o, "release-reservation"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                              >
                                <Unlock className="h-3.5 w-3.5" />
                                <span>Liberar reserva</span>
                              </button>
                            )}
                            {canWrite && o.stock_reserved && (
                              <button
                                type="button"
                                title="Renovar reserva"
                                disabled={busy}
                                onClick={() => { orderAction(o, "renew-reservation"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                <span>Renovar reserva</span>
                              </button>
                            )}
                            {canWrite && o.status === "backorder" && (
                              <button
                                type="button"
                                onClick={() => { openShortages(o); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-amber-700 hover:bg-amber-50"
                              >
                                <PackageCheck className="h-3.5 w-3.5" />
                                <span>Gestionar faltantes</span>
                              </button>
                            )}
                            {canWrite && (o.status === "confirmed" || o.status === "backorder" || o.status === "partially_fulfilled") && (
                              <button
                                type="button"
                                title="Preparar por escaneo"
                                disabled={busy}
                                onClick={() => { orderAction(o, "picking"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-teal-700 hover:bg-teal-50"
                              >
                                <PackageCheck className="h-3.5 w-3.5" />
                                <span>Preparar</span>
                              </button>
                            )}
                            {canWrite && (
                              <button
                                type="button"
                                title="Repetir pedido"
                                disabled={busy}
                                onClick={() => { orderAction(o, "clone"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                              >
                                <Copy className="h-3.5 w-3.5" />
                                <span>Repetir pedido</span>
                              </button>
                            )}
                            {canWrite && !["fulfilled", "cancelled"].includes(o.status) && (
                              <button
                                type="button"
                                title="Cancelar pedido"
                                disabled={busy}
                                onClick={() => { orderAction(o, "cancel"); setOpenMenuId(null); }}
                                className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-red-600 hover:bg-red-50"
                              >
                                <Ban className="h-3.5 w-3.5" />
                                <span>Cancelar pedido</span>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </PaginatedTable>
    </div>
  </div>);
}
