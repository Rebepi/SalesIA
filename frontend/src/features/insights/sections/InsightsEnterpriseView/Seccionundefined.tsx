import type { useInsightsEnterpriseView } from "../../hooks/useInsightsEnterpriseView";


export function Seccionundefined({ activeActionModal, setActiveActionModal, prepareAction, isSubmitting }: { activeActionModal: NonNullable<ReturnType<typeof useInsightsEnterpriseView>["activeActionModal"]>; setActiveActionModal: ReturnType<typeof useInsightsEnterpriseView>["setActiveActionModal"]; prepareAction: ReturnType<typeof useInsightsEnterpriseView>["prepareAction"]; isSubmitting: ReturnType<typeof useInsightsEnterpriseView>["isSubmitting"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
    <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 className="text-base font-bold text-slate-900">
          {activeActionModal.action.title}
        </h3>
        <button
          type="button"
          onClick={() => setActiveActionModal(null)}
          className="text-slate-400 hover:text-slate-600 font-bold"
        >
          ✕
        </button>
      </div>

      <div className="mt-4 space-y-3 text-sm">
        <p className="text-xs text-slate-600">
          {activeActionModal.action.description}
        </p>

        <div className="rounded-xl bg-teal-50 p-3 border border-teal-200 text-xs">
          <span className="font-semibold text-teal-900">Impacto proyectado: </span>
          <span className="text-teal-800">{activeActionModal.action.projected_impact}</span>
        </div>

        <div className="rounded-xl bg-amber-50 p-3 border border-amber-200 text-xs text-amber-900">
          <span className="font-bold">Regla de seguridad: </span>
          <span>Este borrador NO ejecuta transferencias, compras ni cobros financieros automáticamente. Cualquier cambio operativo exige confirmación manual autorizada.</span>
        </div>
      </div>

      <div className="mt-5 flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setActiveActionModal(null)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          Cerrar
        </button>
        <button
          type="button"
          onClick={prepareAction}
          disabled={isSubmitting}
          className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800"
        >
          Iniciar borrador autorizado
        </button>
      </div>
    </div>
  </div>);
}
