import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { X } from "lucide-react";

export function SeccionView_pod({ setModalType, activePod }: { setModalType: ReturnType<typeof useDeliveriesWorkspaceTab>["setModalType"]; activePod: NonNullable<ReturnType<typeof useDeliveriesWorkspaceTab>["activePod"]> }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-bold text-slate-900">Evidencia de Entrega Autorizada (POD)</h3>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-4 space-y-3 text-xs">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Receptor:</p>
          <p className="font-semibold text-slate-900">{activePod.received_by_name}</p>
          {activePod.received_by_id_doc && (
            <p className="font-mono text-[11px] text-slate-500">Doc: {activePod.received_by_id_doc}</p>
          )}
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Fecha y Hora de Entrega:</p>
          <p className="font-semibold text-slate-900">{new Date(activePod.delivered_at).toLocaleString()}</p>
        </div>
        {activePod.signature_data && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-[10px]">
            <p className="text-slate-500 font-sans text-xs">Firma:</p>
            <p className="truncate text-slate-700">{activePod.signature_data}</p>
          </div>
        )}
        {activePod.notes && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-slate-500">Notas:</p>
            <p className="text-slate-800">{activePod.notes}</p>
          </div>
        )}
      </div>
      <div className="flex justify-end pt-4">
        <button onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cerrar</button>
      </div>
    </div>
  </div>);
}
