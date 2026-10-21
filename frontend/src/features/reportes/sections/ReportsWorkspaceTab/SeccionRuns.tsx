import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Download, RefreshCw, AlertTriangle, CheckCircle2, RotateCcw, Printer, Ban } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionRuns({ loadData, loading, runs, isExpired, canExport, handleDownloadRun, setPrintableRun, handleCancelRun, handleRetryRun }: { loadData: ReturnType<typeof useReportsWorkspaceTab>["loadData"]; loading: ReturnType<typeof useReportsWorkspaceTab>["loading"]; runs: ReturnType<typeof useReportsWorkspaceTab>["runs"]; isExpired: ReturnType<typeof useReportsWorkspaceTab>["isExpired"]; handleDownloadRun: ReturnType<typeof useReportsWorkspaceTab>["handleDownloadRun"]; setPrintableRun: ReturnType<typeof useReportsWorkspaceTab>["setPrintableRun"]; handleCancelRun: ReturnType<typeof useReportsWorkspaceTab>["handleCancelRun"]; handleRetryRun: ReturnType<typeof useReportsWorkspaceTab>["handleRetryRun"] } & { canExport: NonNullable<{ canExport?: boolean }["canExport"]> }) {
  return (<section className="space-y-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2"><h2 className="text-base font-semibold text-slate-900">Historial de Ejecuciones Asíncronas</h2><InfoTooltip title="Historial de ejecuciones" description="Muestra cada generación de reporte, su estado, parámetros, formato y archivo resultante." /></div>
      <button
        onClick={loadData}
        disabled={loading}
        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
      >
        <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
        Refrescar estado
      </button>
    </div>

    <div className="pagination-shell">
      <div className="pagination-shell">
        <PaginatedTable className="w-full text-left text-sm">
          <thead className="bg-slate-100 text-xs uppercase text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-3">ID / Reporte</th>
              <th scope="col" className="px-5 py-3">Formato</th>
              <th scope="col" className="px-5 py-3">Estado</th>
              <th scope="col" className="px-5 py-3">Filas / Tamaño</th>
              <th scope="col" className="px-5 py-3">Sello SHA-256</th>
              <th scope="col" className="px-5 py-3">Emisión / Caducidad</th>
              <th scope="col" className="px-5 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {runs.map(run => {
              const expired = isExpired(run.expires_at);
              return (
                <tr key={run.run_id} className="transition hover:bg-slate-50/80">
                  <td className="px-5 py-4">
                    <p className="font-mono text-xs font-bold text-slate-900">{run.run_id}</p>
                    <p className="text-xs text-slate-500">{run.template_code}</p>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-bold uppercase ${run.format === "pdf"
                        ? "bg-red-100 text-red-800"
                        : run.format === "xlsx"
                          ? "bg-emerald-100 text-emerald-800"
                          : run.format === "csv"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-purple-100 text-purple-800"
                        }`}
                    >
                      {run.format}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex flex-col gap-1">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${run.status === "completed"
                          ? "bg-emerald-50 text-emerald-700"
                          : run.status === "failed"
                            ? "bg-red-50 text-red-700"
                            : run.status === "cancelled"
                              ? "bg-slate-100 text-slate-600"
                              : "bg-amber-50 text-amber-700"
                          }`}
                      >
                        {run.status === "completed" && <CheckCircle2 className="h-3 w-3" />}
                        {run.status === "failed" && <AlertTriangle className="h-3 w-3" />}
                        {run.status === "cancelled" && <Ban className="h-3 w-3" />}
                        {(run.status === "processing" || run.status === "queued") && (
                          <RefreshCw className="h-3 w-3 animate-spin" />
                        )}
                        {run.status}
                      </span>
                      {canExport && (run.status === "processing" || run.status === "queued") && (
                        <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full bg-teal-600 transition-all duration-300"
                            style={{ width: `${run.progress_pct}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs tabular-nums text-slate-700">
                    <p className="font-semibold">{run.row_count} filas</p>
                    <p className="text-slate-400">{run.file_size_kb} KB</p>
                  </td>
                  <td className="px-5 py-4">
                    {run.sha256_hash ? (
                      <span
                        className="font-mono text-[11px] text-slate-600"
                        title={run.sha256_hash}
                      >
                        {run.sha256_hash.substring(0, 10)}…{run.sha256_hash.substring(run.sha256_hash.length - 6)}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-600">
                    <p>{new Date(run.created_at).toLocaleTimeString()}</p>
                    {expired ? (
                      <span className="font-semibold text-red-600">Caducado (410)</span>
                    ) : run.expires_at ? (
                      <span className="text-emerald-700">Válido 15 min</span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex justify-end gap-1.5">
                      {run.status === "completed" && (
                        <>
                          <button
                            onClick={() => handleDownloadRun(run)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-teal-50 hover:text-teal-700"
                            title="Descargar archivo privado sellado"
                          >
                            <Download className="h-3.5 w-3.5" />
                            Descargar
                          </button>
                          <button
                            onClick={() => setPrintableRun(run)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
                            title="Vista de impresión empresarial"
                          >
                            <Printer className="h-3.5 w-3.5" />
                          </button>
                        </>
                      )}
                      {(run.status === "processing" || run.status === "queued") && (
                        <button
                          onClick={() => handleCancelRun(run.run_id)}
                          className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-100"
                        >
                          <Ban className="h-3.5 w-3.5" />
                          Cancelar
                        </button>
                      )}
                      {canExport && (run.status === "failed" || run.status === "cancelled") && (
                        <button
                          onClick={() => handleRetryRun(run.run_id)}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-teal-50 hover:text-teal-700"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Reintentar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {runs.length === 0 && (
              <tr>
                <td colSpan={7} className="p-8 text-center text-sm text-slate-500">
                  No hay ejecuciones de reportes registradas. Elige un reporte del catálogo y haz clic en Generar.
                </td>
              </tr>
            )}
          </tbody>
        </PaginatedTable>
      </div>
    </div>
  </section>);
}
