import type { useRefundsWorkspaceTab } from "../../hooks/useRefundsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";

export function SeccionUpdate_status({ activeRefund, setModalType, handleUpdateStatus }: { activeRefund: NonNullable<ReturnType<typeof useRefundsWorkspaceTab>["activeRefund"]>; setModalType: ReturnType<typeof useRefundsWorkspaceTab>["setModalType"]; handleUpdateStatus: ReturnType<typeof useRefundsWorkspaceTab>["handleUpdateStatus"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="font-bold text-slate-900">Transición de Reembolso #{activeRefund.id.slice(0, 8)}</h3>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleUpdateStatus} className="mt-4 space-y-4">
        <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-700 space-y-1">
          <div><span className="font-semibold">Estado actual:</span> {activeRefund.status}</div>
          <div><span className="font-semibold">Importe:</span> {activeRefund.currency} {activeRefund.amount}</div>
        </div>
        <label className="block text-xs font-semibold text-slate-700">
          Nuevo Estado
          <CustomSelect name="status" defaultValue={activeRefund.status} className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs">
            <option value="aprobado">Aprobado (Autorizado por finanzas)</option>
            <option value="enviado">Enviado a pasarela externa</option>
            <option value="pendiente">Pendiente de acreditación banco</option>
            <option value="confirmado">Confirmado (Liquidado)</option>
            <option value="requiere_conciliacion">Requiere conciliación manual (Incertidumbre)</option>
            <option value="fallido">Fallido / Rechazado por banco</option>
          </CustomSelect>
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Referencia de Pasarela / Código Transacción
          <input name="provider_reference" defaultValue={activeRefund.provider_reference || ""} placeholder="re_1N3k0A2eZvKYlo2C" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Motivo de Rechazo o Incidencia (si aplica)
          <input name="failure_reason" defaultValue={activeRefund.failure_reason || ""} placeholder="Tarjeta vencida o cuenta cerrada" className="mt-1 w-full rounded-xl border border-slate-300 p-2.5 text-xs outline-none focus:ring-2 focus:ring-teal-200" />
        </label>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition">Guardar Estado</button>
        </div>
      </form>
    </div>
  </div>);
}
