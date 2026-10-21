import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Calendar, X } from "lucide-react";
import { ReportScheduleBuilder } from "../../components/ReportScheduleBuilder";

export function SeccionNuevaProgramacionDeReporte({ setCreateScheduleModal, schedTemplateCode, setSchedTemplateCode, templates, schedConfig, setSchedConfig, schedTimezone, setSchedTimezone, schedFormat, setSchedFormat, schedEmails, setSchedEmails, handleCreateSchedule, creatingSchedule }: { setCreateScheduleModal: ReturnType<typeof useReportsWorkspaceTab>["setCreateScheduleModal"]; schedTemplateCode: ReturnType<typeof useReportsWorkspaceTab>["schedTemplateCode"]; setSchedTemplateCode: ReturnType<typeof useReportsWorkspaceTab>["setSchedTemplateCode"]; templates: ReturnType<typeof useReportsWorkspaceTab>["templates"]; schedConfig: ReturnType<typeof useReportsWorkspaceTab>["schedConfig"]; setSchedConfig: ReturnType<typeof useReportsWorkspaceTab>["setSchedConfig"]; schedTimezone: ReturnType<typeof useReportsWorkspaceTab>["schedTimezone"]; setSchedTimezone: ReturnType<typeof useReportsWorkspaceTab>["setSchedTimezone"]; schedFormat: ReturnType<typeof useReportsWorkspaceTab>["schedFormat"]; setSchedFormat: ReturnType<typeof useReportsWorkspaceTab>["setSchedFormat"]; schedEmails: ReturnType<typeof useReportsWorkspaceTab>["schedEmails"]; setSchedEmails: ReturnType<typeof useReportsWorkspaceTab>["setSchedEmails"]; handleCreateSchedule: ReturnType<typeof useReportsWorkspaceTab>["handleCreateSchedule"]; creatingSchedule: ReturnType<typeof useReportsWorkspaceTab>["creatingSchedule"] }) {
  return (<div
    role="dialog"
    aria-modal="true"
    aria-labelledby="sched-modal-title"
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
  >
    <div className="app-modal-panel w-full max-w-lg rounded-2xl bg-white shadow-2xl">
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <h2 id="sched-modal-title" className="text-base font-bold text-slate-900">
            Nueva Programación de Reporte
          </h2>
          <p className="text-xs text-slate-500">Elige la frecuencia, fecha de inicio y destinatarios</p>
        </div>
        <button
          onClick={() => setCreateScheduleModal(false)}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="space-y-4 p-6">
        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="sched-tpl-select">
            Plantilla de reporte:
          </label>
          <CustomSelect
            id="sched-tpl-select"
            value={schedTemplateCode}
            onChange={e => setSchedTemplateCode(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            {templates.map(t => (
              <option key={t.code} value={t.code}>
                {t.name} ({t.code})
              </option>
            ))}
          </CustomSelect>
        </div>

        <ReportScheduleBuilder value={schedConfig} onChange={setSchedConfig} />

        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold text-slate-700" htmlFor="sched-tz-input">
              Zona horaria:
            </label>
            <input
              id="sched-tz-input"
              type="text"
              value={schedTimezone}
              onChange={e => setSchedTimezone(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700" htmlFor="sched-fmt-select">
              Formato:
            </label>
            <CustomSelect
              id="sched-fmt-select"
              value={schedFormat}
              onChange={e => setSchedFormat(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
            >
              <option value="xlsx">XLSX (Excel)</option>
              <option value="pdf">PDF (Documento)</option>
              <option value="csv">CSV (Plano RFC 4180)</option>
              <option value="json">JSON</option>
            </CustomSelect>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="sched-emails-input">
            Miembros destinatarios, separados por coma:
          </label>
          <input
            id="sched-emails-input"
            type="text"
            value={schedEmails}
            onChange={e => setSchedEmails(e.target.value)}
            placeholder="gerencia@salesia.enterprise, finanzas@salesia.enterprise"
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          />
          <p className="mt-1 text-[11px] text-slate-400">
            Se entregan avisos dentro del sistema a miembros activos con permiso para el reporte. En blanco: solo el responsable.
          </p>
        </div>
      </div>

      <footer className="flex justify-end gap-2 border-t border-slate-100 px-6 py-4">
        <button
          onClick={() => setCreateScheduleModal(false)}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          onClick={handleCreateSchedule}
          disabled={creatingSchedule}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-800 disabled:opacity-50"
        >
          <Calendar className="h-3.5 w-3.5" />
          {creatingSchedule ? "Guardando..." : "Guardar Programación"}
        </button>
      </footer>
    </div>
  </div>);
}
