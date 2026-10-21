import type { useInsightsEnterpriseView } from "../../hooks/useInsightsEnterpriseView";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";

export function SeccionEvidenciaNumericaReproducible({ setActiveEvidenceModal, activeEvidenceModal }: { setActiveEvidenceModal: ReturnType<typeof useInsightsEnterpriseView>["setActiveEvidenceModal"]; activeEvidenceModal: NonNullable<ReturnType<typeof useInsightsEnterpriseView>["activeEvidenceModal"]> }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
    <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 className="text-base font-bold text-slate-900">
          Evidencia Numérica Reproducible
        </h3>
        <button
          type="button"
          onClick={() => setActiveEvidenceModal(null)}
          className="text-slate-400 hover:text-slate-600 font-bold"
        >
          ✕
        </button>
      </div>

      <div className="mt-4 space-y-3 text-sm">
        <p className="text-xs text-slate-600 font-medium">
          {activeEvidenceModal.evidence}
        </p>

        {activeEvidenceModal.evidence_data && (
          <div className="pagination-shell">
            <PaginatedTable className="min-w-full divide-y divide-slate-200 text-xs">
              <tbody className="divide-y divide-slate-200">
                <tr>
                  <td className="px-3 py-2 font-semibold text-slate-700">Métrica evaluada</td>
                  <td className="px-3 py-2 text-slate-900">{activeEvidenceModal.evidence_data.metric_name}</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 font-semibold text-slate-700">Valor obtenido</td>
                  <td className="px-3 py-2 text-slate-900 font-bold">{activeEvidenceModal.evidence_data.current_value}%</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 font-semibold text-slate-700">Umbral objetivo</td>
                  <td className="px-3 py-2 text-slate-900">{activeEvidenceModal.evidence_data.threshold}%</td>
                </tr>
                {activeEvidenceModal.evidence_data.denominator && (
                  <tr>
                    <td className="px-3 py-2 font-semibold text-slate-700">Denominador base</td>
                    <td className="px-3 py-2 text-slate-900">{activeEvidenceModal.evidence_data.denominator} USD</td>
                  </tr>
                )}
                {activeEvidenceModal.evidence_data.sample_size !== undefined && (
                  <tr>
                    <td className="px-3 py-2 font-semibold text-slate-700">Muestra (n)</td>
                    <td className="px-3 py-2 text-slate-900">{activeEvidenceModal.evidence_data.sample_size}</td>
                  </tr>
                )}
                {activeEvidenceModal.evidence_data.cutoff_date && (
                  <tr>
                    <td className="px-3 py-2 font-semibold text-slate-700">Fecha de corte</td>
                    <td className="px-3 py-2 text-slate-500 font-mono text-[11px]">{activeEvidenceModal.evidence_data.cutoff_date}</td>
                  </tr>
                )}
              </tbody>
            </PaginatedTable>
          </div>
        )}
      </div>

      <div className="mt-5 flex justify-end">
        <button
          type="button"
          onClick={() => setActiveEvidenceModal(null)}
          className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
        >
          Cerrar evidencia
        </button>
      </div>
    </div>
  </div>);
}
