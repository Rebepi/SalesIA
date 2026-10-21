import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertCircle, Clock, ExternalLink, Lock } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";

export function SeccionPedidosEnCurso({ ordersSectionRef, orders, isSupervisorOrAdmin, setOrdersScope, ordersScope, onNavigate, canReadSales, ordersError, loadOrders, currentUserId, branchId, ordersLoading, onOpenOrder, setSelectedOrderModal, baseCurrency }: { ordersSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["ordersSectionRef"]; orders: ReturnType<typeof usePersonalWorkspaceTab>["orders"]; isSupervisorOrAdmin: ReturnType<typeof usePersonalWorkspaceTab>["isSupervisorOrAdmin"]; setOrdersScope: ReturnType<typeof usePersonalWorkspaceTab>["setOrdersScope"]; ordersScope: ReturnType<typeof usePersonalWorkspaceTab>["ordersScope"]; canReadSales: ReturnType<typeof usePersonalWorkspaceTab>["canReadSales"]; ordersError: ReturnType<typeof usePersonalWorkspaceTab>["ordersError"]; loadOrders: ReturnType<typeof usePersonalWorkspaceTab>["loadOrders"]; currentUserId: ReturnType<typeof usePersonalWorkspaceTab>["currentUserId"]; ordersLoading: ReturnType<typeof usePersonalWorkspaceTab>["ordersLoading"]; setSelectedOrderModal: ReturnType<typeof usePersonalWorkspaceTab>["setSelectedOrderModal"] } & { onNavigate: PersonalWorkspaceTabProps["onNavigate"]; branchId: PersonalWorkspaceTabProps["branchId"]; onOpenOrder: PersonalWorkspaceTabProps["onOpenOrder"]; baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]> }) {
  return (<section
    ref={ordersSectionRef}
    id="section-orders"
    className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-4 flex flex-col justify-between"
  >
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          <h3 className="font-bold text-slate-900 dark:text-slate-100">Pedidos en Curso</h3>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-slate-600 dark:text-slate-400">
            {orders.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isSupervisorOrAdmin && (
            <div className="flex items-center gap-1 rounded-xl bg-slate-100 dark:bg-slate-800 p-1 text-xs">
              <button
                type="button"
                onClick={() => setOrdersScope("mine")}
                className={`rounded-lg px-2 py-0.5 font-semibold transition ${ordersScope === "mine" ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
              >
                Míos
              </button>
              <button
                type="button"
                onClick={() => setOrdersScope("all")}
                className={`rounded-lg px-2 py-0.5 font-semibold transition ${ordersScope === "all" ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm" : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
              >
                Todos
              </button>
            </div>
          )}
          {onNavigate && (
            <button
              type="button"
              onClick={() => onNavigate("orders")}
              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 dark:text-teal-400 hover:text-teal-900 dark:hover:text-teal-300"
            >
              Ver todos <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {!canReadSales ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Lock className="h-8 w-8 text-slate-400 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Módulo de pedidos restringido</p>
          <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
            No cuentas con el permiso <code className="font-mono">sales:read</code> para visualizar pedidos.
          </p>
        </div>
      ) : ordersError ? (
        <div className="flex items-center justify-between rounded-xl bg-rose-50 dark:bg-rose-950/40 p-3 text-xs text-rose-800 dark:text-rose-300">
          <span className="flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" /> {ordersError}
          </span>
          <button
            type="button"
            onClick={() => loadOrders(currentUserId, ordersScope, branchId)}
            className="font-bold underline hover:text-rose-900 dark:hover:text-rose-100"
          >
            Reintentar
          </button>
        </div>
      ) : ordersLoading ? (
        <div className="space-y-2 py-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-14 w-full animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Clock className="h-8 w-8 text-slate-300 dark:text-slate-700 stroke-1 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Sin pedidos en curso</p>
          <p className="text-[11px] text-slate-400 mt-1">
            {ordersScope === "mine" ? "No tienes pedidos activos asignados actualmente." : "No hay pedidos activos en la sede seleccionada."}
          </p>
        </div>
      ) : (
        <ul className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
          {orders.map(order => {
            const statusMap: Record<string, { label: string; badge: string }> = {
              draft: { label: "Borrador", badge: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700" },
              pending_approval: { label: "Por Aprobar", badge: "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800" },
              confirmed: { label: "Confirmado", badge: "bg-sky-100 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 border-sky-200 dark:border-sky-800" },
              backorder: { label: "Pendiente Stock", badge: "bg-purple-100 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800" },
              partially_fulfilled: { label: "Parcial", badge: "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800" }
            };
            const statusInfo = statusMap[order.status] || { label: order.status, badge: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700" };

            return (
              <li
                key={order.order_id}
                onClick={() => {
                  if (onOpenOrder) onOpenOrder(order.order_id);
                  else setSelectedOrderModal(order);
                }}
                className="cursor-pointer rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm transition hover:border-teal-400 dark:hover:border-teal-600 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-900 dark:text-slate-100">{order.order_number}</span>
                  <span className="font-bold text-xs tabular-nums text-slate-900 dark:text-slate-100">
                    {formatMoney(order.total_amount, order.currency || baseCurrency)}
                  </span>
                </div>
                <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                  <p className="truncate font-medium max-w-[200px]">
                    {order.customer_name || "Cliente sin nombre"}
                  </p>
                  <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-semibold ${statusInfo.badge}`}>
                    {statusInfo.label}
                  </span>
                </div>
                <div className="mt-1 text-[10px] text-slate-400">
                  {new Date(order.created_at).toLocaleDateString("es-PE", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>

    <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
      Mostrando pedidos pendientes de despacho, facturación o aprobación.
    </p>
  </section>);
}
