import { Panel1 } from "../sections/AuditWorkspaceTab/Panel1";
import { SeccionVisualizadorDeDiferenciasDiffRedactado } from "../sections/AuditWorkspaceTab/SeccionVisualizadorDeDiferenciasDiffRedactado";
export type { AuditLogEntry } from "../types/AuditWorkspaceTab";
export type { AuditWorkspaceTabProps } from "../types/AuditWorkspaceTab";
import { useAuditWorkspaceTab } from "../hooks/useAuditWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { Download, Lock, ShieldCheck } from "lucide-react";
import { AuditWorkspaceTabProps } from "../types/AuditWorkspaceTab";

export function AuditWorkspaceTab({ canWrite = true }: AuditWorkspaceTabProps) {
  const { loading, loadError, search, setSearch, entityFilter, setEntityFilter, selectedDiff, setSelectedDiff, handleVerifyIntegrity, handleExport, filteredLogs } = useAuditWorkspaceTab({ canWrite });
  return (
    <div id="scr-042-audit-workspace" data-testid="scr-042-audit-workspace" className="space-y-6">
      <NavbarSectionHeader view="audit" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">SEGURIDAD</span>
            <h1 className="text-xl font-bold text-slate-900">Pista de Auditoría y Eventos Críticos</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Registro inmutable de actor, acción, entidad, fecha UTC, correlación y diff redactado. Acceso de solo lectura.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleVerifyIntegrity}
            className="inline-flex items-center gap-1.5 rounded-xl border border-teal-200 bg-teal-50 px-3.5 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-100"
          >
            <ShieldCheck className="h-4 w-4" />
            Verificar Cadena Criptográfica
          </button>

          <button
            onClick={handleExport}
            disabled={!canWrite}
            className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-3.5 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Exportación Separada
          </button>
        </div>
      </NavbarSectionHeader>

      {loadError && (
        <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm text-rose-800">
          No se pudo cargar la auditoría: {loadError}
        </div>
      )}

      {loading && (
        <div role="status" className="rounded-xl border border-slate-200 bg-white p-3.5 text-sm text-slate-600">
          Cargando registros de auditoría…
        </div>
      )}

      <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        <Lock className="h-4 w-4 shrink-0 text-slate-500" />
        <span>
          Garantía de inmutabilidad: Los registros de auditoría son de sólo anexado. Las solicitudes de modificación o eliminación son rechazadas con HTTP 405.
        </span>
      </div>

      <Panel1 search={search} setSearch={setSearch} entityFilter={entityFilter} setEntityFilter={setEntityFilter} filteredLogs={filteredLogs} setSelectedDiff={setSelectedDiff} />

      {selectedDiff && (
        <SeccionVisualizadorDeDiferenciasDiffRedactado selectedDiff={selectedDiff} setSelectedDiff={setSelectedDiff} />
      )}
    </div>
  );
}
