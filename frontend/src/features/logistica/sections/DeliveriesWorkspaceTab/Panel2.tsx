import { useState } from "react";
import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { AlertTriangle, ExternalLink, MapPin, MoreHorizontal, Truck, X, Radio, AlertOctagon, Siren } from "lucide-react";

export function Panel2({ onResults, deliveries, canWrite, handleDispatch, handleCancel, setActiveDelivery, setModalType, handleIntercept, handleViewPod }: { onResults: (id: string) => void; deliveries: ReturnType<typeof useDeliveriesWorkspaceTab>["deliveries"]; handleDispatch: ReturnType<typeof useDeliveriesWorkspaceTab>["handleDispatch"]; handleCancel: ReturnType<typeof useDeliveriesWorkspaceTab>["handleCancel"]; setActiveDelivery: ReturnType<typeof useDeliveriesWorkspaceTab>["setActiveDelivery"]; setModalType: ReturnType<typeof useDeliveriesWorkspaceTab>["setModalType"]; handleIntercept: ReturnType<typeof useDeliveriesWorkspaceTab>["handleIntercept"]; handleViewPod: ReturnType<typeof useDeliveriesWorkspaceTab>["handleViewPod"] } & { canWrite: { canWrite: boolean }["canWrite"] }) {
  const resultLabels: Record<string, string> = { partially_delivered: "Entrega parcial", pending_redelivery: "Reentrega pendiente", partially_rejected: "Rechazo parcial", rejected: "Rechazado" };
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  return (<div className="pagination-shell">
    <PaginatedTable className="w-full text-left text-xs">
      <thead className="bg-slate-100 uppercase text-slate-500">
        <tr>
          <th className="px-4 py-3">Nº Entrega / Fecha</th>
          <th className="px-4 py-3">Destinatario y Dirección Snapshot</th>
          <th className="px-4 py-3">Transportista / Tracking</th>
          <th className="px-4 py-3">Costos vs Tarifa</th>
          <th className="px-4 py-3">Fecha Estimada</th>
          <th className="px-4 py-3">Estado / Siguiente Acción</th>
          <th className="px-4 py-3 text-right">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {deliveries.map(del => (
          <tr key={del.id} className="hover:bg-slate-50/60">
            <td className="px-4 py-3 font-medium text-slate-900">
              <div className="font-semibold">#{del.id.slice(0, 8)}</div>
              <span className="text-[10px] text-slate-400">{new Date(del.created_at).toLocaleDateString()}</span>
            </td>
            <td className="px-4 py-3 text-slate-700">
              <div className="font-semibold text-slate-900">{del.recipient_name || "Sin destinatario"}</div>
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <MapPin className="h-3 w-3 shrink-0 text-slate-400" />
                <span>{del.delivery_address || "—"}</span>
              </div>
            </td>
            <td className="px-4 py-3 text-slate-700">
              <div className="font-semibold">{del.carrier || "Transporte Propio"}</div>
              {del.tracking_url ? (
                <a
                  href={del.tracking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 font-mono text-[10px] text-teal-700 underline hover:text-teal-900"
                >
                  {del.tracking_number} <ExternalLink className="h-2.5 w-2.5" />
                </a>
              ) : (
                <span className="font-mono text-[10px] text-slate-400">{del.tracking_number || "—"}</span>
              )}
            </td>
            <td className="px-4 py-3 text-slate-700">
              <div>Cobrado: <b className="text-teal-700">S/ {del.shipping_fee_charged}</b></div>
              <div className="text-[10px] text-slate-500">Costo real: S/ {del.logistics_cost}</div>
            </td>
            <td className="px-4 py-3">
              {del.estimated_delivery_date ? (
                <div>
                  <div className="font-medium text-slate-900">{new Date(del.estimated_delivery_date).toLocaleDateString()}</div>
                  {del.is_guaranteed ? (
                    <span className="inline-flex rounded-full bg-teal-100 px-1.5 py-0.2 text-[9px] font-bold text-teal-800">Garantizada</span>
                  ) : (
                    <span className="inline-flex rounded-full bg-slate-100 px-1.5 py-0.2 text-[9px] font-medium text-slate-600">Estimada</span>
                  )}
                </div>
              ) : (
                <span className="text-slate-400">—</span>
              )}
            </td>
            <td className="px-4 py-3">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-1.5">
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${del.status === "delivered" ? "bg-emerald-100 text-emerald-800" :
                    del.status === "dispatched" ? "bg-blue-100 text-blue-800" :
                      del.status === "cancelled" ? "bg-red-100 text-red-800" :
                        del.status === "incident" || del.status === "failed_attempt" ? "bg-red-100 text-red-800" :
                          "bg-amber-100 text-amber-800"
                    }`}>
                    {resultLabels[del.status] || del.status}
                  </span>
                  {del.is_delayed && (
                    <span className="inline-flex items-center gap-0.5 rounded-full bg-red-600 px-1.5 py-0.5 text-[9px] font-bold text-white">
                      <AlertTriangle className="h-2.5 w-2.5" /> ATRASADA (+{del.delayed_days}d)
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-slate-500">Próx: <b>{del.next_action}</b></span>
              </div>
            </td>
            <td className="px-4 py-3 text-right">
              <div className="flex items-center justify-end gap-1.5">
                {del.status === "ready" && canWrite && (
                  <button
                    onClick={() => handleDispatch(del.id)}
                    className="rounded-lg bg-teal-700 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-teal-800"
                  >
                    Despachar
                  </button>
                )}
                {del.status === "delivered" && (
                  <button
                    onClick={() => handleViewPod(del.id)}
                    className="rounded-lg border border-teal-200 bg-teal-50 px-2.5 py-1 text-[11px] font-semibold text-teal-700 hover:bg-teal-100"
                  >
                    Ver POD
                  </button>
                )}
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setOpenMenuId(openMenuId === del.id ? null : del.id)}
                    className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-500 hover:bg-slate-100"
                    title="Más opciones"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                  {openMenuId === del.id && (
                    <div
                      onMouseLeave={() => setOpenMenuId(null)}
                      className="absolute right-0 top-8 z-40 w-44 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl dark:border-slate-800 dark:bg-slate-900 text-left"
                    >
                      <button type="button" onClick={() => { onResults(del.id); setOpenMenuId(null); }} className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50">Resultado por producto</button>
                      {del.status === "ready" && canWrite && (
                        <button
                          type="button"
                          onClick={() => { handleCancel(del.id); setOpenMenuId(null); }}
                          className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-red-700 hover:bg-red-50"
                        >
                          <X className="h-3.5 w-3.5" />
                          <span>Cancelar</span>
                        </button>
                      )}
                      {(del.status === "dispatched" || del.status === "in_transit" || del.status === "out_for_delivery") && canWrite && (
                        <>
                          <button
                            type="button"
                            onClick={() => { setActiveDelivery(del); setModalType("tracking_event"); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-slate-700 hover:bg-slate-50"
                          >
                            <Radio className="h-3.5 w-3.5" />
                            <span>+ Tracking</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => { setActiveDelivery(del); setModalType("record_pod"); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-emerald-700 hover:bg-emerald-50"
                          >
                            <Truck className="h-3.5 w-3.5" />
                            <span>POD</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => { setActiveDelivery(del); setModalType("incident"); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-amber-800 hover:bg-amber-50"
                          >
                            <AlertOctagon className="h-3.5 w-3.5" />
                            <span>Incidencia</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => { handleIntercept(del.id); setOpenMenuId(null); }}
                            className="flex w-full items-center gap-2 rounded-xl p-2 text-left text-xs text-orange-800 hover:bg-orange-50"
                          >
                            <Siren className="h-3.5 w-3.5" />
                            <span>Interceptar</span>
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </td>
          </tr>
        ))}
        {deliveries.length === 0 && (
          <tr>
            <td colSpan={7} className="py-8 text-center text-slate-400">No hay entregas registradas.</td>
          </tr>
        )}
      </tbody>
    </PaginatedTable>
  </div>);
}
