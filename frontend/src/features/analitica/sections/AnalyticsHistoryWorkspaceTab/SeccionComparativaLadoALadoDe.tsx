import { useId } from "react";
import type { useAnalyticsHistoryWorkspaceTab } from "../../hooks/useAnalyticsHistoryWorkspaceTab";
import { ModalSurface } from "../../../../ui/components/ModalSurface";
import { AnalyticsRunDetails, metricName, resultValue } from "../../components/AnalyticsRunDetails";
type State = ReturnType<typeof useAnalyticsHistoryWorkspaceTab>;
export function SeccionComparativaLadoALadoDe({ setCompareModalOpen, runA, runB }: { setCompareModalOpen: State["setCompareModalOpen"]; runA: NonNullable<State["runA"]>; runB: NonNullable<State["runB"]> }) {
  const title = useId();
  const compatible = runA.analysis_type === runB.analysis_type && runA.variable_name === runB.variable_name && runA.dataset_id === runB.dataset_id && Boolean(runA.dataset_id);
  const keys = [...new Set([...Object.keys(runA.result || {}), ...Object.keys(runB.result || {})])].filter(key => ![runA.result?.[key], runB.result?.[key]].some(value => typeof value === "object" && value !== null));
  return <ModalSurface labelledBy={title} onClose={() => setCompareModalOpen(false)} className="analytics-history-modal analytics-history-modal-wide"><section className="analytics-history-dialog"><header><h2 id={title}>Comparativa de ejecuciones</h2><button type="button" onClick={() => setCompareModalOpen(false)}>Cerrar comparación</button></header><div className="analytics-history-dialog-body">
    {!compatible && <p className="analytics-history-warning">Las ejecuciones usan distinto tipo, variable o dataset, o no tienen un dataset conservado. Sus resultados se muestran como referencia; no representan una comparación equivalente.</p>}
    {runA.dataset_version !== runB.dataset_version && <p className="analytics-history-warning">Se comparan versiones diferentes del dataset. Revisa los cambios de datos antes de interpretar las diferencias.</p>}
    <div className="analytics-history-table"><table><thead><tr><th>Métrica</th><th>{runA.code}</th><th>{runB.code}</th></tr></thead><tbody>{keys.map(key => <tr key={key}><th>{metricName(key)}</th><td>{resultValue(runA.result?.[key])}</td><td>{resultValue(runB.result?.[key])}</td></tr>)}</tbody></table></div>
    <div className="analytics-comparison-columns">{[runA, runB].map(run => <article key={run.id}><h3>{run.code}</h3><AnalyticsRunDetails run={run} /></article>)}</div>
  </div></section></ModalSurface>;
}
