import type { useSystemHealthSupportWorkspaceTab } from "../../hooks/useSystemHealthSupportWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RotateCcw } from "lucide-react";

export function SeccionColaDeIncidenciasYTareas({ failedJobs, handleRetryJob, loading }: { failedJobs: ReturnType<typeof useSystemHealthSupportWorkspaceTab>["failedJobs"]; handleRetryJob: ReturnType<typeof useSystemHealthSupportWorkspaceTab>["handleRetryJob"]; loading: ReturnType<typeof useSystemHealthSupportWorkspaceTab>["loading"] }) {
  return (<div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-base font-bold text-slate-900">Cola de Incidencias y Tareas Fallidas</h2>
        <p className="text-xs text-slate-500">Eventos de outbox o tareas asíncronas que requieren reintento o resolución.</p>
      </div>
    </div>

    <div className="pagination-group">
      <PaginatedTable className="w-full text-left text-xs">
        <thead className="bg-slate-50 font-semibold uppercase text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-2.5">ID Tarea</th>
            <th scope="col" className="px-4 py-2.5">Nombre Tarea</th>
            <th scope="col" className="px-4 py-2.5">Trace ID</th>
            <th scope="col" className="px-4 py-2.5">Detalle Error</th>
            <th scope="col" className="px-4 py-2.5">Estado</th>
            <th scope="col" className="px-4 py-2.5 text-right">Acción Recuperación</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {failedJobs.map((job) => (
            <tr key={job.id} className="hover:bg-slate-50">
              <td className="px-4 py-2.5 font-mono font-bold text-slate-900">{job.id}</td>
              <td className="px-4 py-2.5 font-semibold text-slate-800">{job.task_name}</td>
              <td className="px-4 py-2.5 font-mono text-slate-500">{job.trace_id}</td>
              <td className="px-4 py-2.5 text-rose-700 font-medium max-w-xs truncate" title={job.error_message}>
                {job.error_message}
              </td>
              <td className="px-4 py-2.5">
                <span className={`rounded-full px-2 py-0.5 font-bold ${job.status === "resolved"
                  ? "bg-emerald-50 text-emerald-700"
                  : job.status === "retrying" ? "bg-amber-50 text-amber-700" : "bg-rose-50 text-rose-700"
                  }`}>
                  {job.status === "resolved" ? "Resuelta" : job.status === "retrying" ? "Reintentando" : "Fallida"}
                </span>
              </td>
              <td className="px-4 py-2.5 text-right">
                {job.status === "failed" && (
                  <button
                    onClick={() => handleRetryJob(job.id)}
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-semibold text-teal-700 hover:bg-slate-50 shadow-sm"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Reintentar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </PaginatedTable>
      {!loading && failedJobs.length === 0 && <div className="p-8 text-center text-sm text-slate-500">No hay trabajos fallidos pendientes de recuperación.</div>}
    </div>
  </div>);
}
