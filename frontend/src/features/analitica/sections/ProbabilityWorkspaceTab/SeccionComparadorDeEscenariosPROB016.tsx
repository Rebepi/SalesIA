import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { GitCompare } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionComparadorDeEscenariosPROB016({ selectedComp1, setSelectedComp1, savedAnalyses, selectedComp2, setSelectedComp2, runComparison, compareResult }: { selectedComp1: ReturnType<typeof useProbabilityWorkspaceTab>["selectedComp1"]; setSelectedComp1: ReturnType<typeof useProbabilityWorkspaceTab>["setSelectedComp1"]; savedAnalyses: ReturnType<typeof useProbabilityWorkspaceTab>["savedAnalyses"]; selectedComp2: ReturnType<typeof useProbabilityWorkspaceTab>["selectedComp2"]; setSelectedComp2: ReturnType<typeof useProbabilityWorkspaceTab>["setSelectedComp2"]; runComparison: ReturnType<typeof useProbabilityWorkspaceTab>["runComparison"]; compareResult: ReturnType<typeof useProbabilityWorkspaceTab>["compareResult"] }) {
  return (<article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <header className="border-b border-slate-100 pb-4 dark:border-slate-800">
      <div className="flex items-center gap-2"><h3 className="text-base font-semibold text-slate-900 dark:text-white">Comparador de Escenarios (PROB-016)</h3><InfoTooltip title="Comparador de escenarios" description="Contrasta dos análisis guardados para visualizar cómo cambian probabilidades y resultados bajo distintas condiciones." /></div>
      <p className="text-xs text-slate-500">
        Compara análisis observados vs simulaciones hipotéticas lado a lado.
      </p>
    </header>

    <div className="mt-4 grid grid-cols-2 gap-4">
      <div>
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Escenario 1</label>
        <CustomSelect
          value={selectedComp1}
          onChange={(e) => setSelectedComp1(e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-200 p-2 text-xs dark:border-slate-700 dark:bg-slate-800"
        >
          {savedAnalyses.map((s) => (
            <option key={s.id} value={s.id}>{s.name} ({s.is_simulation ? "Simulación" : "Observado"})</option>
          ))}
        </CustomSelect>
      </div>

      <div>
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Escenario 2</label>
        <CustomSelect
          value={selectedComp2}
          onChange={(e) => setSelectedComp2(e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-200 p-2 text-xs dark:border-slate-700 dark:bg-slate-800"
        >
          {savedAnalyses.map((s) => (
            <option key={s.id} value={s.id}>{s.name} ({s.is_simulation ? "Simulación" : "Observado"})</option>
          ))}
        </CustomSelect>
      </div>
    </div>

    <button
      type="button"
      onClick={runComparison}
      className="mt-3 flex items-center justify-center gap-2 w-full rounded-xl bg-slate-100 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-200 dark:bg-slate-800 dark:text-white"
    >
      <GitCompare className="h-3.5 w-3.5" />
      Comparar Escenarios
    </button>

    {compareResult && (
      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs font-mono dark:border-slate-800 dark:bg-slate-800/60">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="font-sans font-semibold text-slate-800 dark:text-slate-200">
              {compareResult.scenario_1.name}
            </p>
            <p className="text-slate-500">
              {compareResult.comparison.scenario_1_is_simulation ? "[Simulación]" : "[Observado]"}
            </p>
            <p className="mt-1">Prior: {compareResult.scenario_1.probabilities?.prior_a || "N/A"}</p>
            <p>Posterior: {compareResult.scenario_1.probabilities?.posterior_a_given_b || "N/A"}</p>
          </div>

          <div>
            <p className="font-sans font-semibold text-slate-800 dark:text-slate-200">
              {compareResult.scenario_2.name}
            </p>
            <p className="text-slate-500">
              {compareResult.comparison.scenario_2_is_simulation ? "[Simulación]" : "[Observado]"}
            </p>
            <p className="mt-1">Prior: {compareResult.scenario_2.probabilities?.prior_a || "N/A"}</p>
            <p>Posterior: {compareResult.scenario_2.probabilities?.posterior_a_given_b || "N/A"}</p>
          </div>
        </div>

        <div className="mt-3 border-t border-slate-200 pt-2 text-teal-700 dark:text-teal-300">
          Diferencia Posterior: {compareResult.comparison.posterior_diff}
        </div>
      </div>
    )}
  </article>);
}
