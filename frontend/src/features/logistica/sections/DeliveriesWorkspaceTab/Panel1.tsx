import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { AlertTriangle, Filter, Plus, RefreshCw } from "lucide-react";

export function Panel1({ statusFilter, setStatusFilter, carrierFilter, setCarrierFilter, setDelayedOnly, delayedOnly, delayedCount, setRevision, loading, canWrite, openCreateDelivery }: { statusFilter: ReturnType<typeof useDeliveriesWorkspaceTab>["statusFilter"]; setStatusFilter: ReturnType<typeof useDeliveriesWorkspaceTab>["setStatusFilter"]; carrierFilter: ReturnType<typeof useDeliveriesWorkspaceTab>["carrierFilter"]; setCarrierFilter: ReturnType<typeof useDeliveriesWorkspaceTab>["setCarrierFilter"]; setDelayedOnly: ReturnType<typeof useDeliveriesWorkspaceTab>["setDelayedOnly"]; delayedOnly: ReturnType<typeof useDeliveriesWorkspaceTab>["delayedOnly"]; delayedCount: ReturnType<typeof useDeliveriesWorkspaceTab>["delayedCount"]; setRevision: ReturnType<typeof useDeliveriesWorkspaceTab>["setRevision"]; loading: ReturnType<typeof useDeliveriesWorkspaceTab>["loading"]; openCreateDelivery: ReturnType<typeof useDeliveriesWorkspaceTab>["openCreateDelivery"] } & { canWrite: { canWrite: boolean }["canWrite"] }) {
  return (<div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
    <div className="flex flex-wrap items-center gap-3">
      <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
        <Filter className="h-3.5 w-3.5 text-slate-400" />
        Estado:
        <CustomSelect
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-2.5 py-1 text-xs outline-none"
        >
          <option value="">Todos los estados</option>
          <option value="ready">Listo para Despacho</option>
          <option value="dispatched">Despachado</option>
          <option value="in_transit">En Tránsito</option>
          <option value="delivered">Entregado</option>
          <option value="partially_delivered">Entrega parcial</option>
          <option value="pending_redelivery">Reentrega pendiente</option>
          <option value="partially_rejected">Rechazo parcial para devolución</option>
          <option value="rejected">Rechazado para devolución</option>
          <option value="incident">Con Incidencia</option>
          <option value="failed_attempt">Intento Fallido</option>
          <option value="cancelled">Cancelado</option>
        </CustomSelect>
      </label>

      <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
        Transportista:
        <CustomSelect
          value={carrierFilter}
          onChange={e => setCarrierFilter(e.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-2.5 py-1 text-xs outline-none"
        >
          <option value="">Todos los transportistas</option>
          <option value="DHL Express">DHL Express</option>
          <option value="FedEx">FedEx</option>
          <option value="Olva Express">Olva Express</option>
          <option value="Transporte Propio">Transporte Propio</option>
        </CustomSelect>
      </label>

      <button
        onClick={() => setDelayedOnly(v => !v)}
        className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1 text-xs font-semibold transition ${delayedOnly
          ? "bg-red-600 text-white shadow-sm"
          : "border border-red-200 bg-red-50 text-red-700 hover:bg-red-100"
          }`}
      >
        <AlertTriangle className="h-3.5 w-3.5" />
        Solo Atrasadas ({delayedCount})
      </button>
    </div>

    <div className="flex items-center gap-2">
      <button
        onClick={() => setRevision(r => r + 1)}
        disabled={loading}
        aria-label="Actualizar entregas"
        className="group rounded-xl border border-slate-200 bg-white p-2 text-slate-600 transition hover:bg-slate-100 disabled:opacity-50"
      >
        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : "group-hover:rotate-90"}`} />
      </button>
      {canWrite && (
        <button
          onClick={openCreateDelivery}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Preparar Entrega
        </button>
      )}
    </div>
  </div>);
}
