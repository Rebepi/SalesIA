import { AnalyticsExecutionRun } from "../types/AnalyticsHistoryWorkspaceTab";
import { AnalysisApiRecord } from "../types/AnalyticsHistoryWorkspaceTab";

export function toExecutionRun(record: AnalysisApiRecord): AnalyticsExecutionRun {
  const summary = record.result ? Object.entries(record.result).filter(([, value]) => typeof value !== "object").map(([key, value]) => `${key}=${String(value)}`).join(", ") : "Sin resultado";
  return {
    id: record.id,
    code: record.name || record.id,
    analyst_email: record.created_by_name || record.created_by,
    analysis_type: record.analysis_type,
    dataset_name: record.dataset_name || record.dataset_id || "Datos ingresados manualmente",
    dataset_id: record.dataset_id,
    variable_name: record.variable_name,
    result: record.result,
    explanation: record.explanation,
    dataset_version: record.dataset_version,
    parameters: { variable: record.variable_name, transformations: record.transformations_applied || [] },
    status: record.status,
    result_summary: summary,
    algorithm_version: record.algorithm_version,
    created_at: record.created_at,
    is_reproducible: record.status === "completed" && Boolean(record.dataset_id) && ["summary", "mean", "median"].includes(record.analysis_type),
    repeat_unavailable_reason: record.status !== "completed" ? "Solo se pueden repetir análisis completados." : !record.dataset_id ? "Esta ejecución usó datos manuales que no se conservaron. Ejecútala de nuevo desde Estadística o utiliza un dataset versionado." : !["summary", "mean", "median"].includes(record.analysis_type) ? "Ejecuta este tipo de análisis desde su módulo de origen para conservar sus parámetros." : ""
  };
}
