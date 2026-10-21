import { AlertCircle, Tag } from "lucide-react";
import type { useFichaCliente } from "../hooks/useFichaCliente";
import type { FichaClienteProps } from "../types/clientes";
export function ResumenCliente({ model }: FichaClienteProps & { model: ReturnType<typeof useFichaCliente> }) {
  const { customer, quality, segments, statement, setTab } = model;
  return (<div className="space-y-6">
    <div className="customer-purchase-section flex flex-wrap items-center justify-between gap-3">
      <div><h3>Relación comercial</h3><p>{statement?.invoices.length || 0} operaciones registradas · Cliente {customer?.is_active ? "activo" : "archivado"}</p></div>
      <button type="button" className="customer-card-secondary rounded-xl border px-4 py-2 font-semibold" onClick={() => setTab("history")}>Ver compras y pagos</button>
    </div>
    <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-teal-800">Calidad de ficha</span>
          <p className="mt-1 text-2xl font-bold text-slate-900">{quality?.score_percentage ?? 0} %</p>
        </div>
        <div className="h-3 w-40 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full bg-teal-600 transition-all" style={{ width: `${quality?.score_percentage ?? 0}%` }} />
        </div>
      </div>
      {quality?.alerts && quality.alerts.length > 0 && (
        <div className="mt-4 space-y-2 border-t border-slate-200 pt-3 text-xs text-slate-600">
          <p className="font-semibold text-slate-700">Recomendaciones para completar ficha:</p>
          {quality.alerts.map((alt, i) => (
            <div key={i} className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
              <span>{alt}</span>
            </div>
          ))}
        </div>
      )}
    </div>

    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Código interno</span>
        <p className="font-mono text-sm font-semibold">{String(customer?.code ?? "—")}</p>
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Identificación</span>
        <p className="text-sm font-semibold">{String(customer?.doc_type)}: {String(customer?.doc_number)}</p>
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Correo</span>
        <p className="text-sm">{String(customer?.email ?? "Sin registrar")}</p>
      </div>
      <div className="rounded-xl border border-slate-100 p-4">
        <span className="text-xs text-slate-400">Teléfono</span>
        <p className="text-sm">{String(customer?.phone ?? "Sin registrar")}</p>
      </div>
    </div>

    {segments && segments.matched_segments.length > 0 && (
      <div className="rounded-xl border border-teal-100 bg-teal-50/50 p-4">
        <span className="text-xs font-semibold uppercase text-teal-800">Segmentos asignados</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {segments.matched_segments.map(s => (
            <span key={s.id} className="inline-flex items-center gap-1.5 rounded-full border border-teal-200 bg-white px-3 py-1 text-xs font-medium text-teal-800">
              <Tag className="h-3 w-3" />{s.name}
            </span>
          ))}
        </div>
      </div>
    )}
  </div>);
}
