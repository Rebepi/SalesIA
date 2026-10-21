import { SeccionCalidadYVersionesDelDataset } from "../sections/DataQualityPanel/SeccionCalidadYVersionesDelDataset";
import { SeccionCompletitudYTasaDeError } from "../sections/DataQualityPanel/SeccionCompletitudYTasaDeError";
export type { QualityReport } from "../types/DataQualityPanel";
export type { DatasetVersionItem } from "../types/DataQualityPanel";
export type { DatasetVersionDetail } from "../types/DataQualityPanel";
export type { DatasetItem } from "../types/DataQualityPanel";
export type { DataQualityPanelProps } from "../types/DataQualityPanel";
import { useDataQualityPanel } from "../hooks/useDataQualityPanel";
import { AlertTriangle, CheckCircle, Layers, RefreshCw, Activity, Info } from "lucide-react";
import { DataQualityPanelProps } from "../types/DataQualityPanel";

export function DataQualityPanel({ datasetId: initialDatasetId, onVersionCreated, canCalculate = true }: DataQualityPanelProps) {
  const { ConfirmDialogNode, datasets, activeDatasetId, setActiveDatasetId, versions, selectedVersion, setSelectedVersion, detail, loading, actionLoading, statusMessage, errorMessage, rebuildNote, copiedHash, setCopiedHash, handleCreateOperationalDataset, handleGenerateNewVersionAfterCorrection, handleRebuildProjection, q, isZeroRows, completenessDisplay, completenessVal, completenessColor } = useDataQualityPanel({ datasetId: initialDatasetId, onVersionCreated, canCalculate });
  return (
    <section id="scr-034-datasets-workspace" data-testid="scr-034-datasets-workspace" className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm dark:border-slate-800 dark:bg-slate-900" aria-label="Control de calidad del dataset">
      <SeccionCalidadYVersionesDelDataset datasets={datasets} activeDatasetId={activeDatasetId} setActiveDatasetId={setActiveDatasetId} versions={versions} selectedVersion={selectedVersion} setSelectedVersion={setSelectedVersion} handleCreateOperationalDataset={handleCreateOperationalDataset} actionLoading={actionLoading} canCalculate={canCalculate} />

      <div className="flex items-center gap-3 rounded-xl border border-teal-200/60 bg-teal-50/50 px-5 py-3.5 text-xs text-teal-800 dark:border-teal-900/40 dark:bg-teal-950/20 dark:text-teal-300">
        <Info className="h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400" />
        <span>Este bloque de auditoría de datasets es inmutable e independiente de los filtros de sede, categoría o período superiores del tablero.</span>
      </div>

      {errorMessage && (
        <div role="alert" className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-300">
          <AlertTriangle className="h-5 w-5 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {statusMessage && (
        <div role="status" className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-medium text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300">
          <CheckCircle className="h-5 w-5 shrink-0 text-emerald-600" />
          <span>{statusMessage}</span>
        </div>
      )}

      {rebuildNote && (
        <div role="status" className="flex items-center gap-3 rounded-xl border border-teal-200 bg-teal-50 p-4 text-xs font-medium text-teal-800 dark:border-teal-900/40 dark:bg-teal-950/20 dark:text-teal-300">
          <Activity className="h-5 w-5 shrink-0 text-teal-600" />
          <span>{rebuildNote}</span>
        </div>
      )}

      {loading && !detail && (
        <div className="flex items-center justify-center p-8 text-xs text-slate-500">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin text-teal-600" />
          Cargando informe de calidad y versiones...
        </div>
      )}

      {!loading && activeDatasetId && versions.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-800 dark:bg-slate-800/40">
          <p className="text-sm text-slate-600 dark:text-slate-300">Este dataset todavía no tiene una versión inmutable.</p>
          <button
            type="button"
            onClick={handleGenerateNewVersionAfterCorrection}
            disabled={actionLoading || !canCalculate}
            title={!canCalculate ? "Requiere permisos de cálculo y administración de datasets" : undefined}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:opacity-50"
          >
            <Layers className="h-4 w-4" />
            Generar versión inicial
          </button>
        </div>
      )}

      {detail && q && (
        <SeccionCompletitudYTasaDeError q={q} completenessDisplay={completenessDisplay} completenessColor={completenessColor} isZeroRows={isZeroRows} completenessVal={completenessVal} detail={detail} setCopiedHash={setCopiedHash} copiedHash={copiedHash} handleRebuildProjection={handleRebuildProjection} actionLoading={actionLoading} canCalculate={canCalculate} handleGenerateNewVersionAfterCorrection={handleGenerateNewVersionAfterCorrection} />
      )}
      {ConfirmDialogNode}
    </section>
  );
}
