import type { useApprovalsInboxWorkspaceTab } from "../../hooks/useApprovalsInboxWorkspaceTab";


export function SeccionMotivoObligatorioDeRechazo({ handleConfirmReject, rejectionModalItem, rejectionReason, setRejectionReason, setRejectionModalItem, saving }: { handleConfirmReject: ReturnType<typeof useApprovalsInboxWorkspaceTab>["handleConfirmReject"]; rejectionModalItem: NonNullable<ReturnType<typeof useApprovalsInboxWorkspaceTab>["rejectionModalItem"]>; rejectionReason: ReturnType<typeof useApprovalsInboxWorkspaceTab>["rejectionReason"]; setRejectionReason: ReturnType<typeof useApprovalsInboxWorkspaceTab>["setRejectionReason"]; setRejectionModalItem: ReturnType<typeof useApprovalsInboxWorkspaceTab>["setRejectionModalItem"]; saving: ReturnType<typeof useApprovalsInboxWorkspaceTab>["saving"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
    <form onSubmit={handleConfirmReject} className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4">
      <h3 className="font-bold text-slate-900">Motivo Obligatorio de Rechazo</h3>
      <p className="text-xs text-slate-500">
        Indica la justificación para rechazar la solicitud {rejectionModalItem.code}. El solicitante recibirá esta notificación.
      </p>

      <div>
        <label htmlFor="rejection-reason-input" className="block text-xs font-semibold text-slate-700">Justificación</label>
        <textarea
          id="rejection-reason-input"
          required
          rows={3}
          value={rejectionReason}
          onChange={(e) => setRejectionReason(e.target.value)}
          placeholder="El descuento propuesto supera la política autorizada sin garantía de pago inmediato..."
          className="mt-1.5 w-full rounded-xl border border-slate-300 p-2.5 text-xs text-slate-800 outline-none"
        />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={() => setRejectionModalItem(null)}
          className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          type="submit" disabled={saving}
          className="rounded-xl bg-rose-700 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-800"
        >
          Confirmar Rechazo
        </button>
      </div>
    </form>
  </div>);
}
