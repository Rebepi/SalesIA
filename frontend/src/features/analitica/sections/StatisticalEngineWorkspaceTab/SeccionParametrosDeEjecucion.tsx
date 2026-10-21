import type { useStatisticalEngineWorkspaceTab } from "../../hooks/useStatisticalEngineWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Play } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionParametrosDeEjecucion({ selectedDatasetId, setSelectedDatasetId, loadingDatasets, datasets, selectedVariable, setSelectedVariable, selectedDataset, availableVariables, nullPolicy, setNullPolicy, precision, setPrecision, error, handleExecute, canExecute, loading }: { selectedDatasetId: ReturnType<typeof useStatisticalEngineWorkspaceTab>["selectedDatasetId"]; setSelectedDatasetId: ReturnType<typeof useStatisticalEngineWorkspaceTab>["setSelectedDatasetId"]; loadingDatasets: ReturnType<typeof useStatisticalEngineWorkspaceTab>["loadingDatasets"]; datasets: ReturnType<typeof useStatisticalEngineWorkspaceTab>["datasets"]; selectedVariable: ReturnType<typeof useStatisticalEngineWorkspaceTab>["selectedVariable"]; setSelectedVariable: ReturnType<typeof useStatisticalEngineWorkspaceTab>["setSelectedVariable"]; selectedDataset: ReturnType<typeof useStatisticalEngineWorkspaceTab>["selectedDataset"]; availableVariables: ReturnType<typeof useStatisticalEngineWorkspaceTab>["availableVariables"]; nullPolicy: ReturnType<typeof useStatisticalEngineWorkspaceTab>["nullPolicy"]; setNullPolicy: ReturnType<typeof useStatisticalEngineWorkspaceTab>["setNullPolicy"]; precision: ReturnType<typeof useStatisticalEngineWorkspaceTab>["precision"]; setPrecision: ReturnType<typeof useStatisticalEngineWorkspaceTab>["setPrecision"]; error: ReturnType<typeof useStatisticalEngineWorkspaceTab>["error"]; handleExecute: ReturnType<typeof useStatisticalEngineWorkspaceTab>["handleExecute"]; canExecute: ReturnType<typeof useStatisticalEngineWorkspaceTab>["canExecute"]; loading: ReturnType<typeof useStatisticalEngineWorkspaceTab>["loading"] }) {
  return (<div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex items-center gap-2"><h2 className="text-sm font-bold uppercase tracking-wide text-slate-600">Parámetros de Ejecución</h2><InfoTooltip title="Parámetros estadísticos" description="Define el dataset, la variable, el tratamiento de valores nulos y la precisión antes de ejecutar el cálculo." /></div>
    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div>
        <label htmlFor="stat-dataset-select" className="block text-xs font-medium text-slate-700">Dataset de Origen</label>
        <CustomSelect id="stat-dataset-select" value={selectedDatasetId} onChange={(event) => setSelectedDatasetId(event.target.value)} disabled={loadingDatasets || datasets.length === 0} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:bg-slate-100">
          {datasets.length === 0 && <option value="">No hay datasets versionados</option>}
          {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · v{dataset.active_version} · {dataset.row_count} filas</option>)}
        </CustomSelect>
      </div>
      <div>
        <label htmlFor="stat-variable-select" className="block text-xs font-medium text-slate-700">Variable Cuantitativa</label>
        <CustomSelect id="stat-variable-select" value={selectedVariable} onChange={(event) => setSelectedVariable(event.target.value)} disabled={!selectedDataset} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 disabled:bg-slate-100">
          {availableVariables.map((variable) => <option key={variable.name} value={variable.name}>{variable.name}{variable.label !== variable.name ? ` (${variable.label})` : ""}</option>)}
        </CustomSelect>
      </div>
      <div>
        <label htmlFor="stat-null-policy" className="block text-xs font-medium text-slate-700">Tratamiento de Nulos</label>
        <CustomSelect id="stat-null-policy" value={nullPolicy} onChange={(event) => setNullPolicy(event.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800">
          <option value="skip">Omitir nulos</option><option value="error">Detener ante nulos</option><option value="zero">Imputar cero</option>
        </CustomSelect>
      </div>
      <div>
        <label htmlFor="stat-precision-select" className="block text-xs font-medium text-slate-700">Precisión Decimal</label>
        <CustomSelect id="stat-precision-select" value={precision} onChange={(event) => setPrecision(Number(event.target.value))} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800">
          <option value={2}>2 decimales</option><option value={4}>4 decimales</option><option value={6}>6 decimales</option>
        </CustomSelect>
      </div>
    </div>
    {error && <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {!loadingDatasets && datasets.length === 0 && !error && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Crea un dataset y genera al menos una versión antes de ejecutar estadísticas.</div>}
    <div className="mt-5 flex justify-end">
      <button onClick={handleExecute} disabled={!canExecute} className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50">
        <Play className={`h-4 w-4 ${loading ? "animate-pulse" : ""}`} />
        {loading ? "Calculando…" : "Ejecutar Motor Estadístico"}
      </button>
    </div>
  </div>);
}
