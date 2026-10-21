import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";
import { CheckCircle, Info } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionPABPosterior({ bayesResult }: { bayesResult: NonNullable<ReturnType<typeof useProbabilityWorkspaceTab>["bayesResult"]> }) {
  return (<article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 dark:border-slate-800">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
          Inferencia Bayesiana
        </span>
        <div className="flex items-center gap-2"><h3 className="text-xl font-bold text-slate-900 dark:text-white">P(A|B) Posterior: {bayesResult.posterior_a_given_b}</h3><InfoTooltip title="Probabilidad posterior" description="Probabilidad actualizada de que ocurra A después de observar que ocurrió B, calculada con el teorema de Bayes." /></div>
      </div>
      {bayesResult.equivalence_verified && (
        <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
          <CheckCircle className="h-3.5 w-3.5" />
          Equivalencia Exacta Verificada
        </span>
      )}
    </header>

    <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
        <p className="flex items-center gap-1.5 text-xs text-slate-500">Prior P(A) <InfoTooltip title="Probabilidad previa" description="Probabilidad de A antes de incorporar la evidencia B." /></p>
        <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{bayesResult.prior_a}</p>
      </div>
      <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
        <p className="flex items-center gap-1.5 text-xs text-slate-500">Verosimilitud P(B|A) <InfoTooltip title="Verosimilitud" description="Probabilidad de observar B cuando el evento A ocurre." /></p>
        <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{bayesResult.likelihood_b_given_a}</p>
      </div>
      <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60">
        <p className="flex items-center gap-1.5 text-xs text-slate-500">Evidencia P(B) <InfoTooltip title="Evidencia" description="Probabilidad marginal de observar el evento B en todo el universo." /></p>
        <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{bayesResult.evidence_b}</p>
      </div>
      <div className="rounded-xl bg-teal-50 p-4 dark:bg-teal-950/40">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-teal-800 dark:text-teal-300">Posterior P(A|B) <InfoTooltip align="right" title="Posterior" description="Resultado de actualizar la probabilidad de A con la evidencia aportada por B." /></p>
        <p className="mt-1 text-lg font-bold text-teal-900 dark:text-teal-100">{bayesResult.posterior_a_given_b}</p>
      </div>
    </div>

    {bayesResult.direct_count_posterior && (
      <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50/50 p-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/40 dark:text-slate-300">
        <div className="flex items-center justify-between">
          <span>Conteo directo n(A ∩ B) / n(B):</span>
          <span className="font-mono font-semibold">{bayesResult.direct_count_posterior}</span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span>Fórmula P(B|A) × P(A) / P(B):</span>
          <span className="font-mono font-semibold">{bayesResult.posterior_a_given_b}</span>
        </div>
      </div>
    )}

    {bayesResult.smoothing_details && (
      <div className="mt-4 rounded-xl border border-teal-100 bg-teal-50/50 p-4 text-xs text-teal-900 dark:border-teal-900/50 dark:bg-teal-950/30 dark:text-teal-200">
        <p className="font-semibold">Regularización de Laplace aplicada (Alpha = {bayesResult.smoothing_details.alpha})</p>
        <div className="mt-2 grid grid-cols-2 gap-2 font-mono">
          <div>P(A|B) Empírico: {bayesResult.direct_count_posterior || bayesResult.posterior_a_given_b}</div>
          <div>P(A|B) Suavizado: {bayesResult.smoothing_details.smoothed_posterior_a_given_b}</div>
        </div>
      </div>
    )}

    <div className="mt-5 rounded-xl border border-slate-100 bg-slate-50 p-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/40 dark:text-slate-400">
      <div className="flex items-start gap-2">
        <Info className="h-4 w-4 text-teal-600 mt-0.5 flex-shrink-0" />
        <p>{bayesResult.causality_disclaimer}</p>
      </div>
    </div>
  </article>);
}
