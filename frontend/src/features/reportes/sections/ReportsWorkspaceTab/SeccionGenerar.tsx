import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Play, X } from "lucide-react";

export function SeccionGenerar({ launchModalTemplate, setLaunchModalTemplate, launchFormat, setLaunchFormat, launchCurrency, setLaunchCurrency, launchStartDate, setLaunchStartDate, launchEndDate, setLaunchEndDate, launchStatus, setLaunchStatus, handleLaunchReport, launching }: { launchModalTemplate: NonNullable<ReturnType<typeof useReportsWorkspaceTab>["launchModalTemplate"]>; setLaunchModalTemplate: ReturnType<typeof useReportsWorkspaceTab>["setLaunchModalTemplate"]; launchFormat: ReturnType<typeof useReportsWorkspaceTab>["launchFormat"]; setLaunchFormat: ReturnType<typeof useReportsWorkspaceTab>["setLaunchFormat"]; launchCurrency: ReturnType<typeof useReportsWorkspaceTab>["launchCurrency"]; setLaunchCurrency: ReturnType<typeof useReportsWorkspaceTab>["setLaunchCurrency"]; launchStartDate: ReturnType<typeof useReportsWorkspaceTab>["launchStartDate"]; setLaunchStartDate: ReturnType<typeof useReportsWorkspaceTab>["setLaunchStartDate"]; launchEndDate: ReturnType<typeof useReportsWorkspaceTab>["launchEndDate"]; setLaunchEndDate: ReturnType<typeof useReportsWorkspaceTab>["setLaunchEndDate"]; launchStatus: ReturnType<typeof useReportsWorkspaceTab>["launchStatus"]; setLaunchStatus: ReturnType<typeof useReportsWorkspaceTab>["setLaunchStatus"]; handleLaunchReport: ReturnType<typeof useReportsWorkspaceTab>["handleLaunchReport"]; launching: ReturnType<typeof useReportsWorkspaceTab>["launching"] }) {
  return (<div
    role="dialog"
    aria-modal="true"
    aria-labelledby="launch-modal-title"
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
  >
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white shadow-2xl">
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <h2 id="launch-modal-title" className="text-base font-bold text-slate-900">
            Generar: {launchModalTemplate.name}
          </h2>
          <p className="text-xs text-slate-500">Configuración de parámetros y formato para el worker asíncrono</p>
        </div>
        <button
          onClick={() => setLaunchModalTemplate(null)}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="space-y-4 p-6">
        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="launch-format-select">
            Formato de salida:
          </label>
          <CustomSelect
            id="launch-format-select"
            value={launchFormat}
            onChange={e => setLaunchFormat(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            {launchModalTemplate.allowed_formats.map(fmt => (
              <option key={fmt} value={fmt}>
                {fmt.toUpperCase()} {fmt === "pdf" ? "(Documento corporativo)" : fmt === "xlsx" ? "(Libro Excel tipado)" : fmt === "csv" ? "(CSV seguro RFC 4180)" : "(JSON API)"}
              </option>
            ))}
          </CustomSelect>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="launch-currency-select">
            Moneda de consolidación:
          </label>
          <CustomSelect
            id="launch-currency-select"
            value={launchCurrency}
            onChange={e => setLaunchCurrency(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            <option value="USD">USD (Dólares estadounidenses)</option>
            <option value="PEN">PEN (Soles peruanos)</option>
            <option value="EUR">EUR (Euros)</option>
          </CustomSelect>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold text-slate-700" htmlFor="launch-start-date">
              Fecha inicio (opcional):
            </label>
            <input
              id="launch-start-date"
              type="date"
              value={launchStartDate}
              onChange={e => setLaunchStartDate(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700" htmlFor="launch-end-date">
              Fecha fin (opcional):
            </label>
            <input
              id="launch-end-date"
              type="date"
              value={launchEndDate}
              onChange={e => setLaunchEndDate(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="launch-status-select">
            Filtro por estado de documento:
          </label>
          <CustomSelect
            id="launch-status-select"
            value={launchStatus}
            onChange={e => setLaunchStatus(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            {launchModalTemplate.status_filter_support.map(st => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </CustomSelect>
        </div>
      </div>

      <footer className="flex justify-end gap-2 border-t border-slate-100 px-6 py-4">
        <button
          onClick={() => setLaunchModalTemplate(null)}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          onClick={handleLaunchReport}
          disabled={launching}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800 disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5" />
          {launching ? "Iniciando..." : "Crear Trabajo de Reporte"}
        </button>
      </footer>
    </div>
  </div>);
}
