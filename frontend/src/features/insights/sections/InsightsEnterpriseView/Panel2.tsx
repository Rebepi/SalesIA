import type { useInsightsEnterpriseView } from "../../hooks/useInsightsEnterpriseView";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function Panel2({ filteredInsights, selectedIds, setSelectedIds, getSeverityBadgeClass, getStatusBadgeClass, setActiveEvidenceModal, setActiveActionModal, changeStatus, submitFeedback, setFeedbackFeedbackId, feedbackFeedbackId, feedbackComment, setFeedbackComment }: { filteredInsights: ReturnType<typeof useInsightsEnterpriseView>["filteredInsights"]; selectedIds: ReturnType<typeof useInsightsEnterpriseView>["selectedIds"]; setSelectedIds: ReturnType<typeof useInsightsEnterpriseView>["setSelectedIds"]; getSeverityBadgeClass: ReturnType<typeof useInsightsEnterpriseView>["getSeverityBadgeClass"]; getStatusBadgeClass: ReturnType<typeof useInsightsEnterpriseView>["getStatusBadgeClass"]; setActiveEvidenceModal: ReturnType<typeof useInsightsEnterpriseView>["setActiveEvidenceModal"]; setActiveActionModal: ReturnType<typeof useInsightsEnterpriseView>["setActiveActionModal"]; changeStatus: ReturnType<typeof useInsightsEnterpriseView>["changeStatus"]; submitFeedback: ReturnType<typeof useInsightsEnterpriseView>["submitFeedback"]; setFeedbackFeedbackId: ReturnType<typeof useInsightsEnterpriseView>["setFeedbackFeedbackId"]; feedbackFeedbackId: ReturnType<typeof useInsightsEnterpriseView>["feedbackFeedbackId"]; feedbackComment: ReturnType<typeof useInsightsEnterpriseView>["feedbackComment"]; setFeedbackComment: ReturnType<typeof useInsightsEnterpriseView>["setFeedbackComment"] }) {
  return (<div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
    {filteredInsights.length === 0 ? (
      <div className="col-span-full rounded-2xl border border-dashed border-slate-300 p-12 text-center">
        <p className="text-base font-medium text-slate-700">No hay insights para los filtros seleccionados</p>
        <p className="mt-1 text-sm text-slate-500">Ajusta los criterios de gravedad o estado para ver más alertas.</p>
      </div>
    ) : (
      filteredInsights.map((item) => (
        <article
          key={item.id}
          id={`insight-card-${item.id}`}
          className="relative flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
        >
          <div><label className="mb-3 flex items-center gap-2 text-xs"><input type="checkbox" aria-label={`Seleccionar alerta ${item.title}`} checked={selectedIds.includes(item.id)} onChange={event => setSelectedIds(previous => event.target.checked ? [...previous, item.id] : previous.filter(id => id !== item.id))} />Seleccionar alerta</label>
            <div className="flex items-start justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold ${getSeverityBadgeClass(item.severity)}`}>
                  {`Gravedad: ${item.severity.toUpperCase()}`}
                </span>
                <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${getStatusBadgeClass(item.status)}`}>
                  {item.status}
                </span>
                {(item.status === "new" || item.status === "pending") && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-teal-100 px-2 py-0.5 text-[11px] font-bold text-teal-800 motion-safe:animate-pulse">
                    <span className="h-1.5 w-1.5 rounded-full bg-teal-600"></span>
                    NOVEDAD
                  </span>
                )}
              </div>

              <div className="text-right">
                <div className="text-lg font-black text-slate-900 tracking-tight" id={`cifra-clave-${item.id}`}>
                  {item.cifra_clave}
                </div>
                <div className="text-[11px] font-medium text-slate-500">
                  {item.period}
                </div>
              </div>
            </div>

            <div className="mt-3 flex items-start gap-2">
              <h2 className="text-base font-semibold text-slate-900 leading-snug">{item.title}</h2>
              <InfoTooltip align="right" title={item.title} description={item.interpretation || item.observation || "Hallazgo calculado a partir de los datos comerciales disponibles."} />
            </div>

            <div className="mt-3 space-y-2 text-xs text-slate-600 insight-explanation bg-slate-50 p-4 rounded-xl border border-slate-100">
              {item.observation && (
                <div>
                  <strong className="text-slate-800 font-semibold">Observación: </strong>
                  <span>{item.observation}</span>
                </div>
              )}
              {item.interpretation && (
                <div>
                  <strong className="text-slate-800 font-semibold">Interpretación: </strong>
                  <span>{item.interpretation}</span>
                </div>
              )}
              {item.suggested_action && (
                <div>
                  <strong className="text-slate-800 font-semibold">Acción recomendada: </strong>
                  <span>{item.suggested_action}</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                id={`btn-evidence-${item.id}`}
                onClick={() => setActiveEvidenceModal(item)}
                className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
              >
                Ver evidencia numérica
              </button>

              {item.suggested_actions && item.suggested_actions.length > 0 && (
                <button
                  type="button"
                  id={`btn-action-${item.id}`}
                  onClick={() => setActiveActionModal({ insight: item, action: item.suggested_actions![0] })}
                  className="inline-flex items-center gap-1 rounded-md bg-teal-50 px-2.5 py-1.5 text-xs font-semibold text-teal-700 border border-teal-200 transition hover:bg-teal-100"
                >
                  Borrador de acción
                </button>
              )}
              <button
                type="button"
                id={`btn-status-${item.id}`}
                onClick={() => changeStatus(item.id, "dismissed", "Descartado desde el centro de insights")}
                className="inline-flex items-center gap-1 rounded-md bg-slate-50 px-2.5 py-1.5 text-xs font-semibold text-slate-600 border border-slate-200 transition hover:bg-slate-100"
              >
                Descartar
              </button>
            </div>

            <div className="flex items-center gap-1 text-xs">
              <span className="text-slate-400 mr-1">¿Útil?</span>
              <button
                type="button"
                title="Insight útil"
                onClick={() => submitFeedback(item.id, true)}
                className="rounded p-1 text-slate-500 hover:bg-emerald-50 hover:text-emerald-700"
              >
                👍
              </button>
              <button
                type="button"
                title="Insight no útil"
                onClick={() => setFeedbackFeedbackId(item.id)}
                className="rounded p-1 text-slate-500 hover:bg-rose-50 hover:text-rose-700"
              >
                👎
              </button>
            </div>
          </div>

          {feedbackFeedbackId === item.id && (
            <div className="mt-3 pt-3 border-t border-slate-200 flex flex-col gap-2">
              <label htmlFor={`feedback-comment-${item.id}`} className="text-xs font-medium text-slate-700">
                Motivo para calibración humana (opcional):
              </label>
              <div className="flex gap-2">
                <input
                  id={`feedback-comment-${item.id}`}
                  type="text"
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Ej. Precio en promoción autorizada"
                  className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-xs"
                />
                <button
                  type="button"
                  onClick={() => submitFeedback(item.id, false)}
                  className="rounded bg-slate-800 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-700"
                >
                  Enviar
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackFeedbackId(null)}
                  className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </article>
      ))
    )}
  </div>);
}
