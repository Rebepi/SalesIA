import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";

export function SeccionTracking_event({ setModalType, handleAddTrackingEvent }: { setModalType: ReturnType<typeof useDeliveriesWorkspaceTab>["setModalType"]; handleAddTrackingEvent: ReturnType<typeof useDeliveriesWorkspaceTab>["handleAddTrackingEvent"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-bold text-slate-900">Registrar Evento de Seguimiento</h3>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleAddTrackingEvent} className="mt-4 space-y-3">
        <label className="block text-xs font-semibold text-slate-700">
          Código del Evento
          <input name="event_code" required placeholder="IN_TRANSIT_HUB" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Estado Normalizado
          <CustomSelect name="event_status" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
            <option value="in_transit">En Tránsito</option>
            <option value="out_for_delivery">En Reparto</option>
            <option value="failed_attempt">Intento Fallido</option>
            <option value="incident">Incidencia en Ruta</option>
          </CustomSelect>
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Ubicación Actual
          <input name="location" placeholder="Centro de Distribución Lima Norte" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Descripción Detallada
          <input name="description" required placeholder="Paquete clasificado y despachado hacia unidad móvil" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">Registrar Evento</button>
        </div>
      </form>
    </div>
  </div>);
}
