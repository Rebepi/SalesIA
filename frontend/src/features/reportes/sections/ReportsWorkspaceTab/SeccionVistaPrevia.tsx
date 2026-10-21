import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { RefreshCw, X } from "lucide-react";

export function SeccionVistaPrevia({ previewTemplate, setPreviewTemplate, loadingPreview, previewData, handleOpenLaunch }: { previewTemplate: NonNullable<ReturnType<typeof useReportsWorkspaceTab>["previewTemplate"]>; setPreviewTemplate: ReturnType<typeof useReportsWorkspaceTab>["setPreviewTemplate"]; loadingPreview: ReturnType<typeof useReportsWorkspaceTab>["loadingPreview"]; previewData: ReturnType<typeof useReportsWorkspaceTab>["previewData"]; handleOpenLaunch: ReturnType<typeof useReportsWorkspaceTab>["handleOpenLaunch"] }) {
  return (<div
    role="dialog"
    aria-modal="true"
    aria-labelledby="preview-modal-title"
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
  >
    <div className="app-modal-panel max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-2xl">
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <h2 id="preview-modal-title" className="text-base font-bold text-slate-900">
            Vista Previa: {previewTemplate.name}
          </h2>
          <p className="text-xs text-slate-500">Corte rápido para confirmar consulta antes de generación intensiva</p>
        </div>
        <button
          onClick={() => setPreviewTemplate(null)}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="max-h-[calc(90vh-140px)] overflow-y-auto p-6">
        {loadingPreview ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500">
            <RefreshCw className="h-8 w-8 animate-spin text-teal-600" />
            <p className="mt-3 text-sm">Calculando muestra de datos y estimación de tamaño...</p>
          </div>
        ) : previewData ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-teal-100 bg-teal-50/50 p-3.5">
                <p className="text-xs text-teal-700">Filas estimadas</p>
                <p className="mt-1 text-lg font-bold text-teal-900">{previewData.estimated_row_count}</p>
              </div>
              <div className="rounded-xl border border-teal-100 bg-teal-50/50 p-3.5">
                <p className="text-xs text-teal-700">Tamaño estimado</p>
                <p className="mt-1 text-lg font-bold text-teal-900">{previewData.estimated_file_size_kb} KB</p>
              </div>
              <div className="rounded-xl border border-teal-100 bg-teal-50/50 p-3.5">
                <p className="text-xs text-teal-700">Fecha de corte snapshot</p>
                <p className="mt-1 text-xs font-bold text-teal-900">
                  {new Date(previewData.cutoff_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Muestra de Datos ({previewData.sample_rows.length} filas)
              </h3>
              <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      {previewData.columns.map(col => (
                        <th key={col} className="px-3 py-2 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {previewData.sample_rows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        {previewData.columns.map(col => (
                          <td key={col} className="px-3 py-2 tabular-nums text-slate-700">
                            {String(row[col] ?? "—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <footer className="flex justify-end gap-2 border-t border-slate-100 px-6 py-3.5">
        <button
          onClick={() => setPreviewTemplate(null)}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Cerrar
        </button>
        <button
          onClick={() => {
            const tpl = previewTemplate;
            setPreviewTemplate(null);
            handleOpenLaunch(tpl);
          }}
          className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800"
        >
          Continuar y Generar Reporte
        </button>
      </footer>
    </div>
  </div>);
}
