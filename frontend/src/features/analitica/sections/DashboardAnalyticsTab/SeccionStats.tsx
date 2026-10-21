import type { useDashboardAnalyticsTab } from "../../hooks/useDashboardAnalyticsTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { Info, ShieldAlert } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionStats({ setShowSkewnessExplainer, showSkewnessExplainer, summaryData, formatMoney, showAccessibleTables }: { setShowSkewnessExplainer: ReturnType<typeof useDashboardAnalyticsTab>["setShowSkewnessExplainer"]; showSkewnessExplainer: ReturnType<typeof useDashboardAnalyticsTab>["showSkewnessExplainer"]; summaryData: NonNullable<ReturnType<typeof useDashboardAnalyticsTab>["summaryData"]>; formatMoney: ReturnType<typeof useDashboardAnalyticsTab>["formatMoney"]; showAccessibleTables: ReturnType<typeof useDashboardAnalyticsTab>["showAccessibleTables"] }) {
  return (<article className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3 dark:border-slate-800">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="flex items-center gap-2 text-base font-bold text-slate-900 dark:text-white">Estadística Descriptiva y Distribución <InfoTooltip title="Estadística descriptiva" description="Presenta medidas de tendencia, dispersión y distribución calculadas sobre las ventas del período seleccionado." /></h2>
          <button
            type="button"
            onClick={() => setShowSkewnessExplainer(!showSkewnessExplainer)}
            aria-expanded={showSkewnessExplainer}
            title="Ver nota técnica sobre asimetría muestral"
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
          >
            <Info className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-slate-500">
          Histograma de frecuencias relativas, boxplot de cuantiles y detección de valores atípicos mediante regla de Tukey.
        </p>
      </div>
      <span className="text-xs font-mono text-slate-400">
        Muestra: {summaryData.sample_count} ventas confirmadas
      </span>
    </div>

    {showSkewnessExplainer && (
      <div className="mt-3 flex items-start gap-2.5 rounded-xl border border-teal-200/60 bg-teal-50/50 p-3.5 text-xs text-teal-900 dark:border-teal-900/40 dark:bg-teal-950/20 dark:text-teal-300">
        <Info className="h-4 w-4 shrink-0 text-teal-600 dark:text-teal-400 mt-0.5" />
        <div>
          <strong className="block font-semibold">Interpretación de Asimetría Muestral</strong>
          <p className="mt-0.5 text-[11px] leading-relaxed">
            La divergencia entre media y mediana refleja asimetría empírica en el importe de tickets. No implica por sí sola causalidad operativa ni anomalías fraudulentas; describe la concentración natural del ticket de compra.
          </p>
        </div>
      </div>
    )}

    {summaryData.sample_count > 10000 ? (
      <div className="mt-4 flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs font-medium text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-200">
        <ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" />
        <span>
          La muestra supera las 10,000 ventas. Seleccione un período menor (7 días o 30 días) para renderizar la distribución interactiva de alta precisión.
        </span>
      </div>
    ) : (
      <div className="mt-5 grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Histograma de Frecuencias
            </h3>
            <p className="text-[11px] text-slate-400">Distribución de tickets por intervalo de importe</p>
          </div>

          {summaryData.histogram?.bins && summaryData.histogram.bins.length > 0 ? (
            <div className="mt-4 space-y-2.5">
              {summaryData.histogram.bins.map((bin) => {
                const maxBinCount = Math.max(1, ...(summaryData.histogram?.bins?.map((b) => b.count) || [1]));
                const barWidth = Math.round((bin.count / maxBinCount) * 100);
                return (
                  <div key={bin.bin_index} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[11px] text-slate-600 dark:text-slate-400 truncate max-w-[180px]">
                        {bin.interval}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="font-bold tabular-nums text-slate-800 dark:text-slate-200">
                          {bin.count}
                        </span>
                        <span className="text-[10px] text-slate-400 tabular-nums">
                          ({(parseFloat(bin.relative_frequency) * 100).toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                      <div
                        className="h-full bg-teal-600 transition-all duration-300"
                        style={{ width: `${Math.max(2, barWidth)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="py-8 text-center text-xs text-slate-400">Sin datos para histograma.</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Diagrama Boxplot (Cuantiles)
            </h3>
            <p className="text-[11px] text-slate-400">
              Fronteras de Tukey: [Q1 - 1.5*IQR, Q3 + 1.5*IQR] para detección de outliers
            </p>
          </div>

          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-white p-2 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                <span className="text-[10px] text-slate-400">Q1 (25%)</span>
                <p className="mt-0.5 font-bold tabular-nums text-slate-900 dark:text-white">
                  {formatMoney(summaryData.distribution.q1)}
                </p>
              </div>
              <div className="rounded-lg bg-white p-2 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                <span className="text-[10px] text-slate-400">Mediana (Q2)</span>
                <p className="mt-0.5 font-bold tabular-nums text-teal-600 dark:text-teal-400">
                  {formatMoney(summaryData.distribution.median)}
                </p>
              </div>
              <div className="rounded-lg bg-white p-2 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                <span className="text-[10px] text-slate-400">Q3 (75%)</span>
                <p className="mt-0.5 font-bold tabular-nums text-slate-900 dark:text-white">
                  {formatMoney(summaryData.distribution.q3)}
                </p>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span>Valla inferior: <strong>{formatMoney(summaryData.boxplot?.lower_fence)}</strong></span>
                <span>Valla superior: <strong>{formatMoney(summaryData.boxplot?.upper_fence)}</strong></span>
              </div>
              <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2 dark:border-slate-800">
                <span className="text-slate-600 dark:text-slate-300">Valores atípicos detectados:</span>
                <span
                  className={`font-bold tabular-nums ${(summaryData.boxplot?.outliers_count || 0) > 0
                    ? "text-amber-600 dark:text-amber-400"
                    : "text-slate-600 dark:text-slate-400"
                    }`}
                >
                  {summaryData.boxplot?.outliers_count || 0}
                </span>
              </div>
              {summaryData.boxplot?.outliers && summaryData.boxplot.outliers.length > 0 && (
                <p className="mt-1 text-[10px] text-slate-400 truncate" title={summaryData.boxplot.outliers.join(", ")}>
                  Muestra de valores: {summaryData.boxplot.outliers.slice(0, 5).join(", ")}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    )}

    {showAccessibleTables && summaryData.histogram?.bins && (
      <div className="mt-6 pagination-shell">
        <PaginatedTable className="w-full text-left text-xs" aria-label="Tabla accesible de histograma de frecuencias">
          <caption className="sr-only">Distribución de frecuencias por intervalo de ticket</caption>
          <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 dark:bg-slate-800">
            <tr>
              <th scope="col" className="px-3 py-2 font-semibold">Intervalo de Importe</th>
              <th scope="col" className="px-3 py-2 text-right font-semibold">Observaciones (Ventas)</th>
              <th scope="col" className="px-3 py-2 text-right font-semibold">Frecuencia Relativa</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {summaryData.histogram.bins.map((bin) => (
              <tr key={bin.bin_index} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-3 py-2 font-mono">{bin.interval}</td>
                <td className="px-3 py-2 text-right tabular-nums font-semibold">{bin.count}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {(parseFloat(bin.relative_frequency) * 100).toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </PaginatedTable>
      </div>
    )}
  </article>);
}
