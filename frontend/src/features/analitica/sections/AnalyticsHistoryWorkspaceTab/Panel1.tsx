import type { useAnalyticsHistoryWorkspaceTab } from "../../hooks/useAnalyticsHistoryWorkspaceTab";
import { Eye, Play, LoaderCircle } from "lucide-react";
import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { analysisNames, statusNames } from "../../components/AnalyticsRunDetails";

type State = ReturnType<typeof useAnalyticsHistoryWorkspaceTab>;
export function Panel1({ runs, selectedForCompare, toggleSelectForCompare, canWrite, repeatingId, handleRepeatRun, showDetail }: Pick<State, "runs" | "selectedForCompare" | "toggleSelectForCompare" | "repeatingId" | "handleRepeatRun" | "showDetail"> & { canWrite: boolean }) {
  return <div className="analytics-history-table"><table className="w-full text-left text-sm"><thead><tr>{["Comparar", "Análisis", "Tipo / estado", "Dataset y versión", "Autor", "Resultado", "Fecha UTC", "Acciones"].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>{runs.map(run => <tr key={run.id}>
    <td><input type="checkbox" aria-label={`Comparar ${run.code} (${run.id})`} checked={selectedForCompare.includes(run.id)} disabled={!selectedForCompare.includes(run.id) && selectedForCompare.length >= 2} onChange={() => toggleSelectForCompare(run.id)} /></td>
    <td><strong>{run.code}</strong><span className="analytics-history-subtext">{run.variable_name || "Variable no registrada"}</span></td>
    <td>{analysisNames[run.analysis_type] || run.analysis_type}<span className={`analytics-history-status analytics-history-status-${run.status}`}>{statusNames[run.status] || run.status}</span></td>
    <td className="analytics-history-reference">{run.dataset_name}<span className="analytics-history-subtext">Versión {run.dataset_version}</span></td>
    <td className="analytics-history-reference">{run.analyst_email}</td>
    <td><span className="analytics-history-result">{run.result_summary || "Sin métricas resumidas"}</span></td>
    <td className="analytics-history-date">{new Date(run.created_at).toLocaleString("es-PE", { timeZone: "UTC" })}</td>
    <td><div className="analytics-history-row-actions"><IconAction label={`Ver detalle de ${run.code}`} tone="primary" onClick={() => void showDetail(run)}><Eye size={16} /></IconAction>{canWrite && <IconAction label={`Repetir ${run.code}`} disabled={!run.is_reproducible || Boolean(repeatingId)} tone="primary" onClick={() => void handleRepeatRun(run)}>{repeatingId === run.id ? <LoaderCircle size={16} className="animate-spin" /> : <Play size={16} />}</IconAction>}{!run.is_reproducible && <InfoTooltip title="Reejecución no disponible" description={run.repeat_unavailable_reason} interactive align="right" />}</div></td>
  </tr>)}</tbody></table></div>;
}
