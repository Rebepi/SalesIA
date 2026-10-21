import type { useDataQualityPanel } from "../../hooks/useDataQualityPanel";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { AlertTriangle, Layers, RefreshCw, Copy, Check } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";
import { DataQualityPanelProps } from "../../types/DataQualityPanel";

export function SeccionCompletitudYTasaDeError({ q, completenessDisplay, completenessColor, isZeroRows, completenessVal, detail, setCopiedHash, copiedHash, handleRebuildProjection, actionLoading, canCalculate, handleGenerateNewVersionAfterCorrection }: { q: NonNullable<ReturnType<typeof useDataQualityPanel>["q"]>; completenessDisplay: ReturnType<typeof useDataQualityPanel>["completenessDisplay"]; completenessColor: ReturnType<typeof useDataQualityPanel>["completenessColor"]; isZeroRows: ReturnType<typeof useDataQualityPanel>["isZeroRows"]; completenessVal: ReturnType<typeof useDataQualityPanel>["completenessVal"]; detail: NonNullable<ReturnType<typeof useDataQualityPanel>["detail"]>; setCopiedHash: ReturnType<typeof useDataQualityPanel>["setCopiedHash"]; copiedHash: ReturnType<typeof useDataQualityPanel>["copiedHash"]; handleRebuildProjection: ReturnType<typeof useDataQualityPanel>["handleRebuildProjection"]; actionLoading: ReturnType<typeof useDataQualityPanel>["actionLoading"]; handleGenerateNewVersionAfterCorrection: ReturnType<typeof useDataQualityPanel>["handleGenerateNewVersionAfterCorrection"] } & { canCalculate: NonNullable<DataQualityPanelProps["canCalculate"]> }) {
  return (<div className="space-y-6">
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <article className="rounded-xl border border-slate-200 bg-slate-50/80 p-5 sm:p-5.5 dark:border-slate-800 dark:bg-slate-800/50 space-y-1.5 transition-all">
        <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">Total recibidos <InfoTooltip title="Total recibido" description="Cantidad bruta de registros recibidos antes de aplicar reglas de validación y calidad." /></span>
        <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white" data-testid="quality-received">{q.received}</p>
        <span className="text-[11px] text-slate-400">Universo transaccional bruto</span>
      </article>

      <article className="rounded-xl border border-slate-200 bg-slate-50/80 p-5 sm:p-5.5 dark:border-slate-800 dark:bg-slate-800/50 space-y-1.5 transition-all">
        <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">Registros utilizados <InfoTooltip title="Registros utilizados" description="Registros válidos que forman parte de la versión actual del dataset." /></span>
        <p className="mt-1 text-2xl font-bold text-teal-700 dark:text-teal-400" data-testid="quality-used">{q.used}</p>
        <span className="text-[11px] text-slate-400">Grano válido en dataset</span>
      </article>

      <article className="rounded-xl border border-slate-200 bg-slate-50/80 p-5 sm:p-5.5 dark:border-slate-800 dark:bg-slate-800/50 space-y-1.5 transition-all">
        <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">Excluidos con motivo <InfoTooltip title="Registros excluidos" description="Registros omitidos por anulación, falta de alcance o incumplimiento de una regla de calidad." /></span>
        <p className={`mt-1 text-2xl font-bold ${q.excluded > 0 ? "text-amber-600" : "text-slate-700 dark:text-slate-200"}`} data-testid="quality-excluded">{q.excluded}</p>
        <span className="text-[11px] text-slate-400">Anulados o fuera de alcance</span>
      </article>

      <article className="rounded-xl border border-slate-200 bg-slate-50/80 p-5 sm:p-5.5 dark:border-slate-800 dark:bg-slate-800/50 space-y-1.5 transition-all">
        <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">Completitud global <InfoTooltip align="right" title="Completitud global" description="Porcentaje de campos esperados que contienen valores válidos en la versión del dataset." /></span>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-slate-900 dark:text-white" data-testid="quality-completeness">{completenessDisplay}</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
          <div
            className={`h-full ${completenessColor.split(" ")[0]}`}
            style={{ width: `${isZeroRows ? 0 : Math.min(100, Math.max(0, completenessVal))}%` }}
          />
        </div>
      </article>
    </div>

    <div className="rounded-xl border border-slate-200/90 bg-slate-50/40 px-5 py-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/30 dark:text-slate-300">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800 dark:text-slate-100">Checksum determinista SHA-256:</span>
          <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-800 dark:bg-slate-800 dark:text-slate-200" title={detail.sha256_hash || "Sin hash"}>
            {detail.sha256_hash ? detail.sha256_hash.slice(0, 16) + "..." : "Sin hash"}
          </code>
          {detail.sha256_hash && (
            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(detail.sha256_hash);
                setCopiedHash(true);
                setTimeout(() => setCopiedHash(false), 2000);
              }}
              className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              title="Copiar checksum completo al portapapeles"
              aria-label="Copiar checksum completo"
            >
              {copiedHash ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
              {copiedHash ? "Copiado" : "Copiar"}
            </button>
          )}
        </div>
        <div>
          <span className="font-semibold text-slate-800 dark:text-slate-100">Estado de retención: </span>
          <span className="rounded bg-teal-100 px-2 py-0.5 text-[11px] font-semibold text-teal-800 dark:bg-teal-900/50 dark:text-teal-200">{detail.status}</span>
        </div>
      </div>
    </div>

    <section aria-labelledby="variables-quality-title" className="space-y-3">
      <div className="flex items-center gap-2"><h4 id="variables-quality-title" className="text-sm font-bold text-slate-800 dark:text-slate-200">Completitud y tasa de error por variable</h4><InfoTooltip title="Calidad por variable" description="Compara valores ausentes, errores detectados y porcentaje de completitud para cada variable del dataset." /></div>
      {Object.keys(q.variable_completeness || {}).length > 0 ? (
        <div className="space-y-2.5">
          {Object.entries(q.variable_completeness || {}).map(([vName, compPct]) => {
            const nullCount = q.null_counts?.[vName] ?? 0;
            const errRate = q.error_rates?.[vName] ?? 0;
            const barColor = compPct >= 90 ? "bg-teal-600" : compPct >= 70 ? "bg-amber-500" : "bg-rose-500";
            return (
              <div key={vName} className="rounded-xl border border-slate-100 bg-slate-50/60 p-3 dark:border-slate-800 dark:bg-slate-800/30">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">{vName}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-500">Nulos: <strong className="text-slate-700 dark:text-slate-200">{nullCount}</strong></span>
                    <span className="text-[11px] text-slate-500">Tasa de error: <strong className="text-slate-700 dark:text-slate-200">{errRate}%</strong></span>
                    <span className="font-bold text-slate-800 dark:text-slate-100">{compPct}%</span>
                  </div>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                  <div className={`h-full ${barColor}`} style={{ width: `${Math.min(100, Math.max(0, compPct))}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
          No se registran variables auditadas en esta versión del dataset.
        </p>
      )}
    </section>

    {Object.keys(q.excluded_by_reason || {}).length > 0 && (
      <section aria-labelledby="excluded-reasons-title" className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900/40 dark:bg-amber-950/20">
        <h4 id="excluded-reasons-title" className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-900 dark:text-amber-200">
          <AlertTriangle className="h-4 w-4" /> Desglose de registros excluidos por motivo
        </h4>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {Object.entries(q.excluded_by_reason).map(([reason, count]) => (
            <div key={reason} className="flex items-center justify-between rounded-lg bg-white p-2.5 text-xs text-slate-700 shadow-sm dark:bg-slate-800 dark:text-slate-300">
              <span className="font-medium text-slate-800 dark:text-slate-100">
                {reason === "cancelled_status" ? "Ventas anuladas / canceladas" :
                  reason === "missing_amount" ? "Sin importe total válido" :
                    reason === "zero_or_negative_amount" ? "Importe nulo o negativo" :
                      reason === "foreign_currency" ? "Moneda distinta sin conversión" : reason}
              </span>
              <span className="rounded bg-amber-100 px-2 py-0.5 font-bold text-amber-800 dark:bg-amber-900/60 dark:text-amber-200">{count}</span>
            </div>
          ))}
        </div>
      </section>
    )}

    {q.imputation_warnings && q.imputation_warnings.length > 0 && (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-200">
        <strong className="block font-semibold">Advertencias de imputación y calidad:</strong>
        <ul className="mt-1 list-disc space-y-1 pl-4">
          {q.imputation_warnings.map((w, idx) => (
            <li key={idx}>{w}</li>
          ))}
        </ul>
      </div>
    )}

    <section aria-labelledby="sample-preview-title" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 id="sample-preview-title" className="text-sm font-bold text-slate-800 dark:text-slate-200">
          Previsualización de datos
        </h4>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          Muestra representativa ({detail.sample?.length || 0} filas de {detail.row_count} totales · población completa calculada)
        </span>
      </div>
      {detail.sample && detail.sample.length > 0 ? (
        <div className="pagination-shell">
          <PaginatedTable className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 dark:bg-slate-800 dark:text-slate-400">
              <tr>
                {Object.keys(detail.sample[0]).map((col) => (
                  <th key={col} className="px-3 py-2 font-semibold">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {detail.sample.slice(0, 5).map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  {Object.keys(detail.sample[0]).map((col) => (
                    <td key={col} className="px-3 py-2 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                      {row[col] === null ? <span className="italic text-slate-400">null</span> : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </PaginatedTable>
        </div>
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500 dark:border-slate-800">
          Dataset sin observaciones (n=0).
        </p>
      )}
    </section>

    <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5 dark:border-slate-800">
      <div className="max-w-md">
        <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
          Control de versiones inmutables
        </p>
        <p className="text-[11px] text-slate-400">
          Crea una nueva versión inmutable con los datos transaccionales actuales sin alterar el historial existente.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleRebuildProjection}
          disabled={actionLoading || !canCalculate}
          title={!canCalculate ? "Requiere permisos de cálculo y administración de datasets" : undefined}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <RefreshCw className={`h-4 w-4 ${actionLoading ? "animate-spin" : ""}`} />
          Reconstruir proyección
        </button>
        <button
          type="button"
          onClick={handleGenerateNewVersionAfterCorrection}
          disabled={actionLoading || !canCalculate}
          title={!canCalculate ? "Requiere permisos de cálculo y administración de datasets" : undefined}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:opacity-50"
        >
          <Layers className="h-4 w-4" />
          Generar nueva versión
        </button>
      </div>
    </footer>
  </div>);
}
