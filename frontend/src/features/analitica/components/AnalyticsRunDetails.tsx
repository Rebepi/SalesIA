import type { AnalyticsExecutionRun } from "../types/AnalyticsHistoryWorkspaceTab";
export const analysisNames: Record<string, string> = { summary: "Resumen estadístico", mean: "Media", median: "Mediana", variance: "Varianza", stdev: "Desviación estándar" };
export const statusNames: Record<string, string> = { completed: "Completado", processing: "En proceso", failed: "Fallido", cancelled: "Cancelado" };
const metricNames: Record<string, string> = { count: "Observaciones", mean: "Media", median: "Mediana", minimum: "Mínimo", maximum: "Máximo", variance: "Varianza", stdev: "Desviación estándar", null_count: "Valores nulos", null_policy: "Tratamiento de nulos", algorithm_version: "Versión del algoritmo", variable_name: "Variable", tolerance: "Tolerancia", raw_metrics: "Métricas originales", transformed_metrics: "Métricas transformadas", didactic_explanation: "Explicación del cálculo" };
export function metricName(key: string) { return metricNames[key] || key; }
export function resultValue(value: unknown): string { return value === null || value === undefined ? "Sin valor" : typeof value === "object" ? JSON.stringify(value, null, 2) : String(value); }
export function AnalyticsRunDetails({ run }: { run: AnalyticsExecutionRun }) {
  return <div className="analytics-run-detail"><dl className="analytics-run-metadata">{[["Estado", statusNames[run.status] || run.status], ["Tipo", analysisNames[run.analysis_type] || run.analysis_type], ["Dataset", run.dataset_name], ["Versión del dataset", String(run.dataset_version)], ["Variable", run.variable_name || "No registrada"], ["Algoritmo", run.algorithm_version], ["Autor", run.analyst_email], ["Fecha UTC", new Date(run.created_at).toLocaleString("es-PE", { timeZone: "UTC" })]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {run.explanation && <p className="analytics-run-explanation">{run.explanation}</p>}
    <h3>Resultado completo</h3>{run.result ? <dl className="analytics-result-list">{Object.entries(run.result).map(([key, value]) => <div key={key}><dt>{metricName(key)}</dt><dd>{typeof value === "object" && value !== null ? <pre>{resultValue(value)}</pre> : resultValue(value)}</dd></div>)}</dl> : <p>Esta ejecución {run.status === "cancelled" ? "fue cancelada y no conserva un resultado" : "no tiene un resultado disponible"}.</p>}
    <details className="analytics-run-parameters"><summary>Parámetros y transformaciones</summary><pre>{JSON.stringify(run.parameters, null, 2)}</pre></details>
    {!run.is_reproducible && <p className="analytics-run-explanation">{run.repeat_unavailable_reason}</p>}
  </div>;
}
