import { Panel1 } from "../sections/ApprovalsInboxWorkspaceTab/Panel1";
import { SeccionMotivoObligatorioDeRechazo } from "../sections/ApprovalsInboxWorkspaceTab/SeccionMotivoObligatorioDeRechazo";
export type { ApprovalRequestItem } from "../types/ApprovalsInboxWorkspaceTab";
export type { ApprovalsInboxWorkspaceTabProps } from "../types/ApprovalsInboxWorkspaceTab";
import { useApprovalsInboxWorkspaceTab } from "../hooks/useApprovalsInboxWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { AlertTriangle } from "lucide-react";
import { ApprovalsInboxWorkspaceTabProps } from "../types/ApprovalsInboxWorkspaceTab";

export function ApprovalsInboxWorkspaceTab({ canWrite = true }: ApprovalsInboxWorkspaceTabProps) {
  const { approvals, loading, error, rejectionModalItem, setRejectionModalItem, rejectionReason, setRejectionReason, versionConflictItem, setVersionConflictItem, saving, handleApprove, handleConfirmReject, pendingApprovals } = useApprovalsInboxWorkspaceTab({ canWrite });
  return (
    <div id="scr-048-approvals-inbox" data-testid="scr-048-approvals-inbox" className="space-y-6">
      <NavbarSectionHeader view="approvals" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">AUTORIZACIONES</span>
            <h1 className="text-xl font-bold text-slate-900">Bandeja de Aprobaciones</h1>
            {pendingApprovals.length > 0 && (
              <span className="rounded-full bg-teal-700 px-2 py-0.5 text-xs font-bold text-white">
                {pendingApprovals.length} pendientes
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Flujo de autorización jerárquica con revalidación estricta de versión del documento antes de aprobar.
          </p>
        </div>
      </NavbarSectionHeader>

      {loading && <div role="status" className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">Cargando solicitudes de aprobación…</div>}
      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">No se pudieron cargar las aprobaciones: {error}</div>}
      {!loading && !error && approvals.length === 0 && <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-600">No existen solicitudes de aprobación.</div>}

      {versionConflictItem && (
        <div role="alert" className="flex items-start gap-3 rounded-2xl border border-rose-300 bg-rose-50 p-4 text-rose-900 shadow-sm">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
          <div className="flex-1">
            <h4 className="font-bold text-sm">Conflicto de Versión de Documento Detectado</h4>
            <p className="mt-0.5 text-xs leading-relaxed">
              La solicitud «{versionConflictItem.code}» fue emitida sobre la versión v{versionConflictItem.document_version}, pero el documento en el servidor ya se encuentra en v{versionConflictItem.server_document_version}. La aprobación fue bloqueada para prevenir inconsistencias.
            </p>
          </div>
          <button onClick={() => setVersionConflictItem(null)} className="text-rose-700 hover:text-rose-900 text-xs font-semibold">
            Entendido
          </button>
        </div>
      )}

      <Panel1 approvals={approvals} canWrite={canWrite} saving={saving} setRejectionModalItem={setRejectionModalItem} handleApprove={handleApprove} />

      {rejectionModalItem && (
        <SeccionMotivoObligatorioDeRechazo handleConfirmReject={handleConfirmReject} rejectionModalItem={rejectionModalItem} rejectionReason={rejectionReason} setRejectionReason={setRejectionReason} setRejectionModalItem={setRejectionModalItem} saving={saving} />
      )}
    </div>
  );
}
