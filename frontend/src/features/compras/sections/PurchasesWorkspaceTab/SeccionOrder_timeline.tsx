import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { CheckCircle2, X } from "lucide-react";

export function SeccionOrder_timeline({ activeTimeline, setModalType }: { activeTimeline: NonNullable<ReturnType<typeof usePurchasesWorkspaceTab>["activeTimeline"]>; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
    <div className="app-modal-panel w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-bold text-slate-900">Timeline de Proceso · Orden v{activeTimeline.version}</h3>
          <p className="text-[11px] text-slate-500">Siguiente acción recomendada: <span className="font-bold text-teal-700">{activeTimeline.next_recommended_step}</span></p>
        </div>
        <button onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-bold text-slate-800">Saldos por Línea de Compra:</h4>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs">
          {activeTimeline.line_balances.map(l => (
            <div key={l.product_id} className="flex justify-between py-1 border-b border-slate-200 last:border-0">
              <span className="font-medium text-slate-700">Producto {l.product_id.slice(0, 8)}:</span>
              <span className="tabular-nums text-slate-600">
                Ordenado: <b>{l.ordered_quantity}</b> | Recibido: <b>{l.received_quantity}</b> | Pendiente: <b className="text-amber-700">{l.pending_quantity}</b>
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-bold text-slate-800">Hitos del Ciclo:</h4>
        <div className="space-y-1.5">
          {activeTimeline.timeline.map((item, idx) => (
            <div key={idx} className="flex items-center gap-3 rounded-lg border border-slate-100 bg-white p-2.5 text-xs">
              <CheckCircle2 className="h-4 w-4 text-teal-600 shrink-0" />
              <div className="flex-1">
                <div className="font-semibold text-slate-900">{item.stage}</div>
                <div className="text-[10px] text-slate-400">{item.date ? new Date(item.date).toLocaleString() : "Pendiente"} · Estado: {item.status}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex justify-end pt-4">
        <button onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cerrar</button>
      </div>
    </div>
  </div>);
}
