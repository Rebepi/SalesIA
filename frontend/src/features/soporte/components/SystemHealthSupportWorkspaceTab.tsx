import { SeccionColaDeIncidenciasYTareas } from "../sections/SystemHealthSupportWorkspaceTab/SeccionColaDeIncidenciasYTareas";
export type { SystemServiceStatus } from "../types/SystemHealthSupportWorkspaceTab";
export type { FailedJobItem } from "../types/SystemHealthSupportWorkspaceTab";
export type { SystemHealthSupportWorkspaceTabProps } from "../types/SystemHealthSupportWorkspaceTab";
import { useSystemHealthSupportWorkspaceTab } from "../hooks/useSystemHealthSupportWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { Download, Lock } from "lucide-react";
import { SystemHealthSupportWorkspaceTabProps } from "../types/SystemHealthSupportWorkspaceTab";

export function SystemHealthSupportWorkspaceTab({ canWrite: _canWrite = true, isTechAdmin = false }: SystemHealthSupportWorkspaceTabProps) {
  const { services, failedJobs, loading, loadError, handleRetryJob, handleDownloadDiagnostic } = useSystemHealthSupportWorkspaceTab({ canWrite: _canWrite, isTechAdmin });
  return (
    <div id="scr-049-system-health-support" data-testid="scr-049-system-health-support" className="space-y-6">
      <NavbarSectionHeader view="health" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">SOPORTE</span>
            <h1 className="text-xl font-bold text-slate-900">Estado de Servicios, Diagnóstico y Soporte</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Observabilidad técnica, cola de incidencias y acciones autorizadas. Ocultamiento de secretos de infraestructura.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadDiagnostic}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            <Download className="h-4 w-4" />
            Descargar Informe Diagnóstico
          </button>
        </div>
      </NavbarSectionHeader>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Consultando el estado real de los servicios...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}

      {!isTechAdmin && (
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          <Lock className="h-4 w-4 text-slate-500 shrink-0" />
          <span>
            Vista comercial protegida: Cadenas de conexión, credenciales de base de datos y topología interna de servidores permanecen ocultas conforme a las políticas de seguridad.
          </span>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {services.map((svc) => (
          <div key={svc.name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase">{svc.name}</span>
              <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold ${svc.status === "healthy" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : svc.status === "degraded" ? "border-amber-200 bg-amber-50 text-amber-700" : "border-rose-200 bg-rose-50 text-rose-700"}`}>
                {svc.status === "healthy" ? "Operativo" : svc.status === "degraded" ? "Degradado" : "No disponible"}
              </span>
            </div>
            <p className="mt-3 text-2xl font-bold text-slate-900">{svc.latency_ms} ms</p>
            <p className="text-xs text-slate-400">Latencia observada · Objetivo SLO: {svc.uptime_pct}</p>
            <div className="mt-4 border-t border-slate-100 pt-3 text-[11px] text-slate-500">
              {svc.details}
            </div>
          </div>
        ))}
      </div>

      <SeccionColaDeIncidenciasYTareas failedJobs={failedJobs} handleRetryJob={handleRetryJob} loading={loading} />
    </div>
  );
}
