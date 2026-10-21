import type { useAuditWorkspaceTab } from "../../hooks/useAuditWorkspaceTab";
import { ShieldCheck, X } from "lucide-react";

export function SeccionVisualizadorDeDiferenciasDiffRedactado({ selectedDiff, setSelectedDiff }: { selectedDiff: NonNullable<ReturnType<typeof useAuditWorkspaceTab>["selectedDiff"]>; setSelectedDiff: ReturnType<typeof useAuditWorkspaceTab>["setSelectedDiff"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
    <div className="app-modal-panel w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="font-mono text-xs font-bold text-teal-700">{selectedDiff.action}</span>
          <h3 className="font-bold text-slate-900">Visualizador de Diferencias (Diff Redactado)</h3>
        </div>
        <button onClick={() => setSelectedDiff(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
          <X className="h-5 w-5" />
        </button>
      </div>

      <p className="mt-2 text-xs text-slate-500">
        Trace ID: <span className="font-mono text-slate-800">{selectedDiff.trace_id}</span> · Actor: <span className="font-semibold text-slate-800">{selectedDiff.actor_email}</span>
      </p>

      <div className="mt-4 rounded-xl bg-slate-900 p-4 font-mono text-xs text-emerald-400 overflow-x-auto max-h-72">
        <pre>{JSON.stringify(selectedDiff.payload_diff, null, 2)}</pre>
      </div>

      <div className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
        <ShieldCheck className="h-3.5 w-3.5 text-teal-600" />
        <span>Campos sensibles enmascarados conforme a la política de privacidad.</span>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={() => setSelectedDiff(null)}
          className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Cerrar Visor
        </button>
      </div>
    </div>
  </div>);
}
