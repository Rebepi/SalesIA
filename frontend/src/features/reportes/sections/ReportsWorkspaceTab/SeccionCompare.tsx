import type { useReportsWorkspaceTab } from "../../hooks/useReportsWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { GitCompare } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionCompare({ compareRunA, setCompareRunA, runs, compareRunB, setCompareRunB, handleCompareRuns, canExport, comparing, comparisonResult }: { compareRunA: ReturnType<typeof useReportsWorkspaceTab>["compareRunA"]; setCompareRunA: ReturnType<typeof useReportsWorkspaceTab>["setCompareRunA"]; runs: ReturnType<typeof useReportsWorkspaceTab>["runs"]; compareRunB: ReturnType<typeof useReportsWorkspaceTab>["compareRunB"]; setCompareRunB: ReturnType<typeof useReportsWorkspaceTab>["setCompareRunB"]; handleCompareRuns: ReturnType<typeof useReportsWorkspaceTab>["handleCompareRuns"]; comparing: ReturnType<typeof useReportsWorkspaceTab>["comparing"]; comparisonResult: ReturnType<typeof useReportsWorkspaceTab>["comparisonResult"] } & { canExport: NonNullable<{ canExport?: boolean }["canExport"]> }) {
  return (<section className="space-y-6">
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2"><h2 className="text-base font-semibold text-slate-900">Comparación de Cortes y Reconstrucción Auditada</h2><InfoTooltip title="Comparación de cortes" description="Compara dos ejecuciones del mismo reporte para identificar diferencias entre períodos o reconstrucciones." /></div>
      <p className="mt-1 text-xs text-slate-500">
        Compara dos ejecuciones para verificar idoneidad de corte temporal, integridad de filas y regresión estadística.
      </p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="compare-run-a">
            Ejecución Base (A):
          </label>
          <CustomSelect
            id="compare-run-a"
            value={compareRunA}
            onChange={e => setCompareRunA(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            <option value="">Selecciona una ejecución...</option>
            {runs.map(r => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} — {r.template_code} ({r.format.toUpperCase()} · {r.row_count} filas)
              </option>
            ))}
          </CustomSelect>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700" htmlFor="compare-run-b">
            Ejecución de Contraste (B):
          </label>
          <CustomSelect
            id="compare-run-b"
            value={compareRunB}
            onChange={e => setCompareRunB(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-2.5 text-xs text-slate-900 outline-none focus:border-teal-500"
          >
            <option value="">Selecciona una ejecución...</option>
            {runs.map(r => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} — {r.template_code} ({r.format.toUpperCase()} · {r.row_count} filas)
              </option>
            ))}
          </CustomSelect>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={handleCompareRuns}
          disabled={!canExport || comparing || !compareRunA || !compareRunB}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:opacity-50"
        >
          <GitCompare className="h-4 w-4" />
          {comparing ? "Comparando..." : "Comparar ejecuciones"}
        </button>
      </div>
    </div>

    {comparisonResult && (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><h3 className="text-sm font-bold text-slate-900">Resultados de Comparación</h3><InfoTooltip title="Resultado de comparación" description="Resume las variaciones encontradas entre los dos cortes seleccionados y su impacto." /></div>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Integridad de Hash SHA-256</p>
            <p
              className={`mt-1 text-sm font-bold ${comparisonResult.identical_hash ? "text-emerald-700" : "text-amber-700"
                }`}
            >
              {comparisonResult.identical_hash ? "Idéntico (100% Coincidente)" : "Diferente (Contenido variado)"}
            </p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Delta de Filas</p>
            <p className="mt-1 text-sm font-bold text-slate-900">
              {comparisonResult.rows_delta > 0 ? `+${comparisonResult.rows_delta}` : comparisonResult.rows_delta} filas
            </p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Diferencia de Ventana de Corte</p>
            <p className="mt-1 text-sm font-bold text-slate-900">
              {comparisonResult.cutoff_delta_seconds} segundos
            </p>
          </div>
        </div>
      </div>
    )}
  </section>);
}
