import { SeccionParametrosDeEjecucion } from "../sections/StatisticalEngineWorkspaceTab/SeccionParametrosDeEjecucion";
export type { StatisticalEngineWorkspaceTabProps } from "../types/StatisticalEngineWorkspaceTab";
import { useStatisticalEngineWorkspaceTab } from "../hooks/useStatisticalEngineWorkspaceTab";
import { PaginatedTable } from "../../../ui/components/PaginatedTable";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { Download } from "lucide-react";
import { InfoTooltip } from "../../../ui/components/InfoTooltip";
import { StatisticalEngineWorkspaceTabProps } from "../types/StatisticalEngineWorkspaceTab";
import { Metric } from "../support/StatisticalEngineWorkspaceTab";
import { TraceRow } from "../support/StatisticalEngineWorkspaceTab";

export function StatisticalEngineWorkspaceTab({ canWrite = true }: StatisticalEngineWorkspaceTabProps) {
  const { datasets, selectedDatasetId, setSelectedDatasetId, selectedVariable, setSelectedVariable, nullPolicy, setNullPolicy, precision, setPrecision, loadingDatasets, loading, error, result, selectedDataset, availableVariables, handleExecute, handleExportMemory, canExecute } = useStatisticalEngineWorkspaceTab({ canWrite });
  return (
    <div id="scr-036-statistics-workspace" data-testid="scr-036-statistics-workspace" className="space-y-6">
      <NavbarSectionHeader view="statistics" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">ANALYTICS</span>
            <h1 className="text-xl font-bold text-slate-900">Motor Estadístico Descriptivo</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">Cálculo determinístico de media, mediana, varianza y simetría sobre una versión inmutable del dataset (motor STATS_V2_PYTHON_EXACT con algoritmo online Welford).</p>
        </div>
        <button onClick={handleExportMemory} disabled={!result} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50">
          <Download className="h-4 w-4" />
          Exportar Memoria de Cálculo
        </button>
      </NavbarSectionHeader>

      <SeccionParametrosDeEjecucion selectedDatasetId={selectedDatasetId} setSelectedDatasetId={setSelectedDatasetId} loadingDatasets={loadingDatasets} datasets={datasets} selectedVariable={selectedVariable} setSelectedVariable={setSelectedVariable} selectedDataset={selectedDataset} availableVariables={availableVariables} nullPolicy={nullPolicy} setNullPolicy={setNullPolicy} precision={precision} setPrecision={setPrecision} error={error} handleExecute={handleExecute} canExecute={canExecute} loading={loading} />

      {result ? <>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Media Aritmética" value={result.mean} detail="Sensible a valores extremos" />
          <Metric label="Mediana Robusta" value={result.median} detail="Percentil 50" accent />
          <Metric label="Desviación Estándar" value={result.stdev} detail={`Varianza: ${result.variance}`} />
          <Metric label="Diagnóstico de Asimetría" value={result.symmetry_diagnosis} detail={result.skewness} compact />
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-2"><h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Explicación e Interpretación</h3><InfoTooltip title="Interpretación estadística" description="Explica en lenguaje natural qué significan las medidas calculadas para la variable seleccionada." /></div><p className="mt-2 text-sm leading-relaxed text-slate-700">{result.explanation}</p></div>
        <div className="pagination-group">
          <div className="flex items-center gap-2"><h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Ficha Técnica y Trazabilidad</h3><InfoTooltip title="Trazabilidad del cálculo" description="Identifica el dataset, observaciones, precisión y versión del algoritmo usados para reproducir el resultado." /></div>
          <div className="mt-4 pagination-shell"><PaginatedTable className="w-full text-left text-xs"><tbody className="divide-y divide-slate-100">
            <TraceRow label="Dataset y versión" value={`${selectedDataset?.name} · v${result.dataset_version}`} />
            <TraceRow label="Observaciones utilizadas" value={String(result.n)} strong />
            <TraceRow label="Valores excluidos" value={String(result.excluded_count)} />
            <TraceRow label="Rango mínimo / máximo" value={`${result.min} / ${result.max}`} />
            <TraceRow label="Precisión numérica" value={`${result.precision} decimales · ROUND_HALF_EVEN`} />
            <TraceRow label="Algoritmo" value={result.algorithm} accent />
            <TraceRow label="Versión del algoritmo" value={result.algorithm_version} accent strong />
          </tbody></PaginatedTable></div>
        </div>
      </> : <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center text-sm text-slate-600">Selecciona una versión de dataset y ejecuta el motor para obtener resultados trazables.</div>}
    </div>
  );
}
