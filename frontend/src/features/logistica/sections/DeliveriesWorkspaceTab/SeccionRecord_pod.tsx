import type { useDeliveriesWorkspaceTab } from "../../hooks/useDeliveriesWorkspaceTab";
import { X } from "lucide-react";

export function SeccionRecord_pod({ setModalType, handleRecordPod }: { setModalType: ReturnType<typeof useDeliveriesWorkspaceTab>["setModalType"]; handleRecordPod: ReturnType<typeof useDeliveriesWorkspaceTab>["handleRecordPod"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-bold text-slate-900">Registrar Prueba de Entrega (POD)</h3>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleRecordPod} className="mt-4 space-y-3">
        <label className="block text-xs font-semibold text-slate-700">
          Nombre de Quien Recibe
          <input name="received_by_name" required placeholder="Nombre completo" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Documento de Identidad (DNI/CE)
          <input name="received_by_id_doc" placeholder="DNI 12345678" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Firma Digital o Hash de Conformidad
          <input name="signature_data" placeholder="HASH_FIRMA_ELECTRONICA" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          URL de Fotografía de Entrega (Protegida)
          <input name="photo_url" placeholder="https://storage.empresa.pe/pod/evidencia.jpg" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Observaciones del Receptor
          <input name="notes" placeholder="Recepción conforme sin observaciones" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">Motivo de aceptación fuera del horario reservado, si corresponde<input name="outside_window_reason" maxLength={2000} className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" /></label>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" className="rounded-xl bg-emerald-700 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-800">Confirmar Entrega</button>
        </div>
      </form>
    </div>
  </div>);
}
