import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";
import { Scale } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionPruebaDeHipotesisDeDos({ htCount1, setHtCount1, htTotal1, setHtTotal1, htCount2, setHtCount2, htTotal2, setHtTotal2, runHypothesisTest, hypoResult }: { htCount1: ReturnType<typeof useProbabilityWorkspaceTab>["htCount1"]; setHtCount1: ReturnType<typeof useProbabilityWorkspaceTab>["setHtCount1"]; htTotal1: ReturnType<typeof useProbabilityWorkspaceTab>["htTotal1"]; setHtTotal1: ReturnType<typeof useProbabilityWorkspaceTab>["setHtTotal1"]; htCount2: ReturnType<typeof useProbabilityWorkspaceTab>["htCount2"]; setHtCount2: ReturnType<typeof useProbabilityWorkspaceTab>["setHtCount2"]; htTotal2: ReturnType<typeof useProbabilityWorkspaceTab>["htTotal2"]; setHtTotal2: ReturnType<typeof useProbabilityWorkspaceTab>["setHtTotal2"]; runHypothesisTest: ReturnType<typeof useProbabilityWorkspaceTab>["runHypothesisTest"]; hypoResult: ReturnType<typeof useProbabilityWorkspaceTab>["hypoResult"] }) {
  return (<article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <header className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wider text-teal-600">Semana 08 · Inferencia Avanzada</span>
        <div className="flex items-center gap-2"><h3 className="text-base font-bold text-slate-900 dark:text-white">Prueba de Hipótesis de Dos Proporciones</h3><InfoTooltip title="Prueba de dos proporciones" description="Evalúa si la diferencia observada entre dos proporciones es estadísticamente significativa." /></div>
      </div>
      <Scale className="h-5 w-5 text-teal-600" />
    </header>

    <div className="mt-4 grid grid-cols-2 gap-4">
      <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50">
        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Grupo 1 (A)</p>
        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
          <div>
            <label className="text-slate-500">Casos</label>
            <input
              type="number"
              value={htCount1}
              onChange={(e) => setHtCount1(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-200 p-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
          <div>
            <label className="text-slate-500">Total N1</label>
            <input
              type="number"
              value={htTotal1}
              onChange={(e) => setHtTotal1(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-200 p-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/50">
        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Grupo 2 (B)</p>
        <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
          <div>
            <label className="text-slate-500">Casos</label>
            <input
              type="number"
              value={htCount2}
              onChange={(e) => setHtCount2(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-200 p-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
          <div>
            <label className="text-slate-500">Total N2</label>
            <input
              type="number"
              value={htTotal2}
              onChange={(e) => setHtTotal2(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-200 p-1.5 dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
        </div>
      </div>
    </div>

    <button
      type="button"
      onClick={runHypothesisTest}
      className="mt-4 w-full rounded-xl border border-slate-300 bg-white py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
    >
      Ejecutar Z-Test de Proporciones
    </button>

    {hypoResult && (
      <div className="mt-5 space-y-3 rounded-xl border border-teal-100 bg-teal-50/40 p-4 text-xs dark:border-teal-900 dark:bg-teal-950/30">
        <div className="flex items-center justify-between font-semibold">
          <span>Decisión:</span>
          <span className="text-teal-800 dark:text-teal-200">{hypoResult.decision}</span>
        </div>
        <div className="grid grid-cols-3 gap-2 font-mono">
          <div>Z-score: {hypoResult.z_statistic}</div>
          <div>p-valor: {hypoResult.p_value}</div>
          <div>Dif: {hypoResult.difference}</div>
        </div>
        <div className="border-t border-teal-200/50 pt-2 text-slate-600 dark:text-slate-400">
          <p className="font-medium text-slate-800 dark:text-slate-200">Aclaración metodológica sobre p-valor:</p>
          <p className="mt-1">{hypoResult.didactic_explanation}</p>
        </div>
      </div>
    )}
  </article>);
}
