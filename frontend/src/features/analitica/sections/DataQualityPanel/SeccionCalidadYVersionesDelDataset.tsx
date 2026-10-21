import type { useDataQualityPanel } from "../../hooks/useDataQualityPanel";
import { NavbarSectionHeader } from "../../../../ui/components/NavbarSectionHeader";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Database } from "lucide-react";
import { DataQualityPanelProps } from "../../types/DataQualityPanel";

export function SeccionCalidadYVersionesDelDataset({ datasets, activeDatasetId, setActiveDatasetId, versions, selectedVersion, setSelectedVersion, handleCreateOperationalDataset, actionLoading, canCalculate }: { datasets: ReturnType<typeof useDataQualityPanel>["datasets"]; activeDatasetId: ReturnType<typeof useDataQualityPanel>["activeDatasetId"]; setActiveDatasetId: ReturnType<typeof useDataQualityPanel>["setActiveDatasetId"]; versions: ReturnType<typeof useDataQualityPanel>["versions"]; selectedVersion: ReturnType<typeof useDataQualityPanel>["selectedVersion"]; setSelectedVersion: ReturnType<typeof useDataQualityPanel>["setSelectedVersion"]; handleCreateOperationalDataset: ReturnType<typeof useDataQualityPanel>["handleCreateOperationalDataset"]; actionLoading: ReturnType<typeof useDataQualityPanel>["actionLoading"] } & { canCalculate: NonNullable<DataQualityPanelProps["canCalculate"]> }) {
  return (<NavbarSectionHeader view="datasets" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-5 dark:border-slate-800">
    <div className="flex items-center gap-3">
      <div className="rounded-xl bg-teal-50 p-2.5 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300">
        <Database className="h-6 w-6" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Calidad y versiones del dataset</h3>
          <span className="rounded-md bg-teal-100 px-2 py-0.5 text-xs font-semibold text-teal-800 dark:bg-teal-900/60 dark:text-teal-200">DSET-019</span>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">Auditoría de integridad, completitud por variable y versionado inmutable reproducible.</p>
      </div>
    </div>

    <div className="flex flex-wrap items-center gap-3">
      {datasets.length > 0 ? (
        <>
          <label htmlFor="select-dataset" className="text-xs font-medium text-slate-500">Dataset:</label>
          <CustomSelect
            id="select-dataset"
            value={activeDatasetId}
            onChange={(e) => setActiveDatasetId(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>{d.name} (grano: {d.grain})</option>
            ))}
          </CustomSelect>

          {versions.length > 0 && (
            <>
              <label htmlFor="select-version" className="text-xs font-medium text-slate-500">Versión:</label>
              <CustomSelect
                id="select-version"
                value={selectedVersion ?? ""}
                onChange={(e) => setSelectedVersion(Number(e.target.value))}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {versions.map((v) => (
                  <option key={v.version} value={v.version}>
                    v{v.version} ({v.row_count} filas · {v.row_count === 0 ? "N/A" : `${v.completeness_pct}%`})
                  </option>
                ))}
              </CustomSelect>
            </>
          )}
        </>
      ) : (
        <button
          onClick={handleCreateOperationalDataset}
          disabled={actionLoading || !canCalculate}
          title={!canCalculate ? "Requiere permisos de cálculo y administración de datasets" : undefined}
          className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-teal-800 disabled:opacity-50"
        >
          <Database className="h-4 w-4" />
          Crear dataset operacional
        </button>
      )}
    </div>
  </NavbarSectionHeader>);
}
