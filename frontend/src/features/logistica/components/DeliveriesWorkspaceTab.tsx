import { useState } from "react";
import { DeliveryResultsDialog } from "./DeliveryResultsDialog";
import { DeliveryWindowsPanel } from "./DeliveryWindowsPanel";
import { DeliveryRoutesPanel } from "./DeliveryRoutesPanel";
import { Panel1 } from "../sections/DeliveriesWorkspaceTab/Panel1";
import { Panel2 } from "../sections/DeliveriesWorkspaceTab/Panel2";
import { SeccionCreate_delivery } from "../sections/DeliveriesWorkspaceTab/SeccionCreate_delivery";
import { SeccionTracking_event } from "../sections/DeliveriesWorkspaceTab/SeccionTracking_event";
import { SeccionRecord_pod } from "../sections/DeliveriesWorkspaceTab/SeccionRecord_pod";
import { SeccionView_pod } from "../sections/DeliveriesWorkspaceTab/SeccionView_pod";
import { useDeliveriesWorkspaceTab } from "../hooks/useDeliveriesWorkspaceTab";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { X } from "lucide-react";

export function DeliveriesWorkspaceTab({ canWrite }: { canWrite: boolean }) {
  const [resultsDelivery, setResultsDelivery] = useState<string | null>(null);
  const { deliveries, delayedCount, delayedOnly, setDelayedOnly, statusFilter, setStatusFilter, carrierFilter, setCarrierFilter, loading, error, setRevision, activeDelivery, setActiveDelivery, activePod, modalType, setModalType, eligibleSales, warehouses, deliveryCurrency, carrierMode, setCarrierMode, openCreateDelivery, handleCreateDelivery, handleDispatch, handleAddTrackingEvent, handleRecordPod, handleViewPod, handleRecordIncident, handleCancel, handleIntercept } = useDeliveriesWorkspaceTab({ canWrite });
  return (
    <div id="scr-028-deliveries-tab" className="space-y-6">
      <Panel1 statusFilter={statusFilter} setStatusFilter={setStatusFilter} carrierFilter={carrierFilter} setCarrierFilter={setCarrierFilter} setDelayedOnly={setDelayedOnly} delayedOnly={delayedOnly} delayedCount={delayedCount} setRevision={setRevision} loading={loading} canWrite={canWrite} openCreateDelivery={openCreateDelivery} />

      {error && <div role="alert" className="rounded-xl bg-red-50 p-4 text-xs text-red-800">{error}</div>}

      <Panel2 onResults={setResultsDelivery} deliveries={deliveries} canWrite={canWrite} handleDispatch={handleDispatch} handleCancel={handleCancel} setActiveDelivery={setActiveDelivery} setModalType={setModalType} handleIntercept={handleIntercept} handleViewPod={handleViewPod} />

      {resultsDelivery && <DeliveryResultsDialog deliveryId={resultsDelivery} canWrite={canWrite} onClose={() => setResultsDelivery(null)} onChanged={() => setRevision(value => value + 1)} />}

      <DeliveryWindowsPanel canWrite={canWrite} onChanged={() => setRevision(value => value + 1)} />

      <DeliveryRoutesPanel canWrite={canWrite} onChanged={() => setRevision(value => value + 1)} />

      {modalType === "create_delivery" && (
        <SeccionCreate_delivery setModalType={setModalType} handleCreateDelivery={handleCreateDelivery} eligibleSales={eligibleSales} warehouses={warehouses} carrierMode={carrierMode} setCarrierMode={setCarrierMode} deliveryCurrency={deliveryCurrency} />
      )}

      {modalType === "tracking_event" && activeDelivery && (
        <SeccionTracking_event setModalType={setModalType} handleAddTrackingEvent={handleAddTrackingEvent} />
      )}

      {modalType === "record_pod" && activeDelivery && (
        <SeccionRecord_pod setModalType={setModalType} handleRecordPod={handleRecordPod} />
      )}

      {modalType === "view_pod" && activePod && (
        <SeccionView_pod setModalType={setModalType} activePod={activePod} />
      )}

      {modalType === "incident" && activeDelivery && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900">Reportar Incidencia Logística</h3>
              <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
            </div>
            <form onSubmit={handleRecordIncident} className="mt-4 space-y-3">
              <label className="block text-xs font-semibold text-slate-700">
                Tipo de Incidencia
                <CustomSelect name="incident_type" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
                  <option value="FAILED_ATTEMPT">Intento Fallido (Destinatario ausente)</option>
                  <option value="DAMAGE">Daño en Traslado</option>
                  <option value="LOSS">Extravío</option>
                  <option value="RESCHEDULE">Reprogramación de Entrega</option>
                </CustomSelect>
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Descripción Detallada
                <input name="description" required placeholder="Motivo o situación encontrada" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
              </label>
              <label className="block text-xs font-semibold text-slate-700">
                Nueva Fecha Reprogramada (Opcional)
                <input name="rescheduled_date" type="datetime-local" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
              </label>
              <div className="flex justify-end gap-2 pt-3">
                <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
                <button type="submit" className="rounded-xl bg-amber-700 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-800">Registrar Incidencia</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
