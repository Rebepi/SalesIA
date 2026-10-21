import { ReportScheduleControls } from "../../components/ReportScheduleControls";
import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { Play, Calendar, XCircle } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { describeReportSchedule } from "../../components/ReportScheduleBuilder";

export function SeccionSchedules({ canExport, setCreateScheduleModal, schedules, handleExecuteScheduleNow, handleDeleteSchedule, loadData }: { loadData: ReturnType<typeof useReportsWorkspaceTab>["loadData"]; setCreateScheduleModal: ReturnType<typeof useReportsWorkspaceTab>["setCreateScheduleModal"]; schedules: ReturnType<typeof useReportsWorkspaceTab>["schedules"]; handleExecuteScheduleNow: ReturnType<typeof useReportsWorkspaceTab>["handleExecuteScheduleNow"]; handleDeleteSchedule: ReturnType<typeof useReportsWorkspaceTab>["handleDeleteSchedule"] } & { canExport: NonNullable<{ canExport?: boolean }["canExport"]> }) {
  return (<section className="space-y-4">
    <div className="flex items-center justify-between">
      <div>
        <div className="flex items-center gap-2"><h2 className="text-base font-semibold text-slate-900">Programaciones de Reportes Periódicos</h2><InfoTooltip title="Reportes programados" description="Configura generaciones automáticas según una frecuencia, zona horaria, formato y destinatarios autorizados." /></div>
        <p className="text-xs text-slate-500">
          Programaciones diarias, semanales o mensuales con zona horaria y destinatarios autorizados.
        </p>
      </div>
      {canExport && <button
        onClick={() => setCreateScheduleModal(true)}
        className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800"
      >
        <Calendar className="h-3.5 w-3.5" />
        Nueva Programación
      </button>}
    </div>

    <div className="grid gap-4 md:grid-cols-2">
      {schedules.map(sched => (
        <div
          key={sched.schedule_id}
          className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-slate-700">{sched.schedule_id}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${sched.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"
                  }`}
              >
                {sched.is_active ? "Activo" : "Inactivo"}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2"><h3 className="text-sm font-bold text-slate-900">{sched.template_code}</h3><InfoTooltip align="right" title={`Programación ${sched.template_code}`} description="Resume la frecuencia y configuración de esta ejecución automática de reporte." /></div>
            <div className="mt-3 space-y-1.5 text-xs text-slate-600">
              <div className="flex justify-between">
                <span className="text-slate-400">Frecuencia:</span>
                <span className="font-mono font-bold text-teal-700">{describeReportSchedule(sched.schedule)}</span>
              </div>{sched.next_run_at && <p className="text-xs">Próxima ejecución: {new Date(sched.next_run_at).toLocaleString("es-PE", { timeZone: sched.timezone })}</p>}{sched.error_message && <p role="alert" className="rounded-lg bg-amber-50 p-2 text-xs text-amber-900">{sched.error_message}</p>}
              <div className="flex justify-between">
                <span className="text-slate-400">Zona horaria:</span>
                <span className="font-medium text-slate-800">{sched.timezone}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Formato:</span>
                <span className="font-semibold uppercase text-slate-800">{sched.format}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Destinatarios:</span>
                <span className="max-w-[200px] truncate text-slate-800" title={sched.recipient_emails.join(", ")}>
                  {sched.recipient_emails.join(", ")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Ejecuciones:</span>
                <span className="font-semibold text-slate-800">{sched.runs_count}</span>
              </div>
            </div>
          </div>

          {canExport && <div className="mt-4 flex items-center justify-end gap-2 border-t border-slate-100 pt-3">
            <button
              onClick={() => handleExecuteScheduleNow(sched.schedule_id)}
              className="inline-flex items-center gap-1 rounded-lg border border-teal-200 bg-teal-50 px-2.5 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100"
            >
              <Play className="h-3 w-3" />
              Ejecutar ahora
            </button>
            <button
              onClick={() => handleDeleteSchedule(sched.schedule_id)}
              className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50"
            >
              <XCircle className="h-3 w-3" />
              Eliminar
            </button>
          </div>}
          {canExport && <ReportScheduleControls schedule={sched} onSaved={() => { void loadData(); }} />}
        </div>
      ))}
      {schedules.length === 0 && (
        <div className="col-span-2 rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
          No hay programaciones periódicas activas. Haz clic en Nueva Programación para registrar una.
        </div>
      )}
    </div>
  </section>);
}
