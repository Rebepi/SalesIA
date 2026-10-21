import { Panel1 } from "../sections/InsightsEnterpriseView/Panel1";
import { Panel2 } from "../sections/InsightsEnterpriseView/Panel2";
import { SeccionEvidenciaNumericaReproducible } from "../sections/InsightsEnterpriseView/SeccionEvidenciaNumericaReproducible";
import { Seccionundefined } from "../sections/InsightsEnterpriseView/Seccionundefined";
export type { InsightActionDraft } from "../types/InsightsEnterpriseView";
export type { InsightEvidenceData } from "../types/InsightsEnterpriseView";
export type { InsightItem } from "../types/InsightsEnterpriseView";
export type { InsightsEnterpriseViewProps } from "../types/InsightsEnterpriseView";
import { useInsightsEnterpriseView } from "../hooks/useInsightsEnterpriseView";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { InsightActionsDialog } from "./InsightActionsDialog";
import { InsightsEnterpriseViewProps } from "../types/InsightsEnterpriseView";

export function InsightsEnterpriseView({
  insights,
  onStatusChange,
  onBulkRead,
  onFeedback
}: InsightsEnterpriseViewProps) {
  const { loading, loadError, selectedSeverity, setSelectedSeverity, selectedStatus, setSelectedStatus, activeEvidenceModal, setActiveEvidenceModal, activeActionModal, setActiveActionModal, feedbackFeedbackId, setFeedbackFeedbackId, feedbackComment, setFeedbackComment, selectedIds, setSelectedIds, actionsOpen, setActionsOpen, setRevision, isSubmitting, toast, displayedInsights, filteredInsights, getSeverityBadgeClass, getStatusBadgeClass, handleBulkReadClick, submitFeedback, changeStatus, prepareAction } = useInsightsEnterpriseView({ insights, onStatusChange, onBulkRead, onFeedback });
  return (
    <div id="scr-039-insights-feed" data-testid="scr-039-insights-feed" className="space-y-6">
      <NavbarSectionHeader view="insights" className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">
              Centro de Insights Determinísticos
            </h1>
            <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700 border border-teal-200">
              F11 Enterprise
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Detección estructurada de rentabilidad, alertas basadas en evidencia numérica y acciones sugeridas no financieras.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            id="btn-insights-bulk-read"
            onClick={handleBulkReadClick}
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-teal-500"
          >
            <span>Marcar todos como leídos</span>
          </button>
        </div>
      </NavbarSectionHeader>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Cargando insights empresariales...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}

      {actionsOpen && <InsightActionsDialog ids={selectedIds} onClose={() => setActionsOpen(false)} onSaved={() => { setActionsOpen(false); setSelectedIds([]); setRevision(value => value + 1); toast.success("Alertas actualizadas", "Los cambios se guardaron y las tareas ya están disponibles en Mi trabajo."); }} />}
      <div className="flex flex-wrap items-center gap-3 text-xs"><label className="flex items-center gap-2"><input type="checkbox" checked={filteredInsights.length > 0 && filteredInsights.every(item => selectedIds.includes(item.id))} onChange={event => setSelectedIds(event.target.checked ? filteredInsights.map(item => item.id) : [])} />Seleccionar alertas visibles</label><button type="button" disabled={!selectedIds.length || isSubmitting} onClick={() => setActionsOpen(true)} className="rounded-xl border px-3 py-2 font-semibold text-teal-700 disabled:opacity-40">Gestionar selección ({selectedIds.length})</button></div>
      <Panel1 selectedSeverity={selectedSeverity} setSelectedSeverity={setSelectedSeverity} selectedStatus={selectedStatus} setSelectedStatus={setSelectedStatus} filteredInsights={filteredInsights} displayedInsights={displayedInsights} />

      <Panel2 filteredInsights={filteredInsights} selectedIds={selectedIds} setSelectedIds={setSelectedIds} getSeverityBadgeClass={getSeverityBadgeClass} getStatusBadgeClass={getStatusBadgeClass} setActiveEvidenceModal={setActiveEvidenceModal} setActiveActionModal={setActiveActionModal} changeStatus={changeStatus} submitFeedback={submitFeedback} setFeedbackFeedbackId={setFeedbackFeedbackId} feedbackFeedbackId={feedbackFeedbackId} feedbackComment={feedbackComment} setFeedbackComment={setFeedbackComment} />

      {activeEvidenceModal && (
        <SeccionEvidenciaNumericaReproducible setActiveEvidenceModal={setActiveEvidenceModal} activeEvidenceModal={activeEvidenceModal} />
      )}

      {activeActionModal && (
        <Seccionundefined activeActionModal={activeActionModal} setActiveActionModal={setActiveActionModal} prepareAction={prepareAction} isSubmitting={isSubmitting} />
      )}
    </div>
  );
}
