import { Panel1 } from "../sections/ProbabilityWorkspaceTab/Panel1";
import { SeccionDefinicionDeUniversoYEventos } from "../sections/ProbabilityWorkspaceTab/SeccionDefinicionDeUniversoYEventos";
import { SeccionPABPosterior } from "../sections/ProbabilityWorkspaceTab/SeccionPABPosterior";
import { SeccionTablaDeContingencia2x2Y } from "../sections/ProbabilityWorkspaceTab/SeccionTablaDeContingencia2x2Y";
import { SeccionPruebaDeHipotesisDeDos } from "../sections/ProbabilityWorkspaceTab/SeccionPruebaDeHipotesisDeDos";
import { SeccionComparadorDeEscenariosPROB016 } from "../sections/ProbabilityWorkspaceTab/SeccionComparadorDeEscenariosPROB016";
import { useProbabilityWorkspaceTab } from "../hooks/useProbabilityWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { CustomSelect } from "../../../ui/components/CustomSelect";

export function ProbabilityWorkspaceTab() {
  const { activeMode, setActiveMode, numberMode, setNumberMode, entityUniverse, setEntityUniverse, period, setPeriod, sampleSpace, setSampleSpace, eventACount, setEventACount, eventBCount, setEventBCount, intersectionCount, setIntersectionCount, priorA, setPriorA, likelihoodA, setLikelihoodA, evidenceB, setEvidenceB, smoothingEnabled, setSmoothingEnabled, alphaVal, setAlphaVal, probResult, bayesResult, hypoResult, savedAnalyses, analysisName, setAnalysisName, loading, errorMsg, htCount1, setHtCount1, htTotal1, setHtTotal1, htCount2, setHtCount2, htTotal2, setHtTotal2, selectedComp1, setSelectedComp1, selectedComp2, setSelectedComp2, compareResult, conditionA, setConditionA, conditionB, setConditionB, thresholdAmount, setThresholdAmount, syncing, syncLiveCounts, calculateEmpirical, calculateManual, runHypothesisTest, saveAnalysis, duplicateAsSimulation, runComparison } = useProbabilityWorkspaceTab();
  return (
    <div id="scr-037-probability-workspace" data-testid="scr-037-probability-workspace" className="space-y-8 pb-12">
      <div id="scr-038-bayes-workspace" data-testid="scr-038-bayes-workspace" className="hidden" aria-hidden="true" />
      <NavbarSectionHeader view="probability" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700 dark:bg-teal-950 dark:text-teal-300">
              Fase 09 · Motor Probabilístico
            </span>
            <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              Axiomas de Kolmogórov & Bayes
            </span>
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Inferencia y Probabilidad Comercial
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Definición axiomática de universo, probabilidad condicional P(A|B) e inferencia bayesiana reproducible.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Condición A</label>
            <CustomSelect
              id="sync-condition-a"
              value={conditionA}
              onChange={(e) => setConditionA(e.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="with_balance">Con ventas (A = compró)</option>
              <option value="high_amount">Monto alto (A = {">"}umbral)</option>
              <option value="credit">A crédito</option>
              <option value="paid">Estado pagado</option>
            </CustomSelect>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Condición B</label>
            <CustomSelect
              id="sync-condition-b"
              value={conditionB}
              onChange={(e) => setConditionB(e.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="high_amount">Monto alto (B = {">"}umbral)</option>
              <option value="multiple_purchases">Compras múltiples</option>
              <option value="credit">A crédito</option>
              <option value="paid">Estado pagado</option>
            </CustomSelect>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Umbral S/</label>
            <input
              id="sync-threshold"
              type="number"
              min={0}
              value={thresholdAmount}
              onChange={(e) => setThresholdAmount(e.target.value)}
              className="w-28 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <button
            type="button"
            id="btn-sync-live-counts"
            onClick={syncLiveCounts}
            disabled={syncing}
            className="inline-flex items-center gap-2 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-800 transition hover:bg-teal-100 disabled:opacity-60 dark:border-teal-800 dark:bg-teal-900/40 dark:text-teal-200"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Sincronizando…" : "Sincronizar con sistema"}
          </button>
        </div>
      </NavbarSectionHeader>

      {errorMsg && (
        <div role="alert" className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
          <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
          <div className="text-sm">
            <p className="font-semibold">Inconsistencia o error detectado</p>
            <p className="mt-1">{errorMsg}</p>
          </div>
        </div>
      )}

      <Panel1 setActiveMode={setActiveMode} activeMode={activeMode} setNumberMode={setNumberMode} numberMode={numberMode} smoothingEnabled={smoothingEnabled} setSmoothingEnabled={setSmoothingEnabled} alphaVal={alphaVal} />

      <div className="grid gap-8 lg:grid-cols-12">
        <SeccionDefinicionDeUniversoYEventos entityUniverse={entityUniverse} setEntityUniverse={setEntityUniverse} period={period} setPeriod={setPeriod} activeMode={activeMode} sampleSpace={sampleSpace} setSampleSpace={setSampleSpace} eventACount={eventACount} setEventACount={setEventACount} eventBCount={eventBCount} setEventBCount={setEventBCount} intersectionCount={intersectionCount} setIntersectionCount={setIntersectionCount} numberMode={numberMode} priorA={priorA} setPriorA={setPriorA} likelihoodA={likelihoodA} setLikelihoodA={setLikelihoodA} evidenceB={evidenceB} setEvidenceB={setEvidenceB} smoothingEnabled={smoothingEnabled} alphaVal={alphaVal} setAlphaVal={setAlphaVal} loading={loading} calculateEmpirical={calculateEmpirical} calculateManual={calculateManual} analysisName={analysisName} setAnalysisName={setAnalysisName} saveAnalysis={saveAnalysis} savedAnalyses={savedAnalyses} duplicateAsSimulation={duplicateAsSimulation} />

        <section className="space-y-6 lg:col-span-7">
          {bayesResult && (
            <SeccionPABPosterior bayesResult={bayesResult} />
          )}

          {probResult && probResult.contingency_table && (
            <SeccionTablaDeContingencia2x2Y probResult={probResult} contingencyTable={probResult.contingency_table} />
          )}

          <SeccionPruebaDeHipotesisDeDos htCount1={htCount1} setHtCount1={setHtCount1} htTotal1={htTotal1} setHtTotal1={setHtTotal1} htCount2={htCount2} setHtCount2={setHtCount2} htTotal2={htTotal2} setHtTotal2={setHtTotal2} runHypothesisTest={runHypothesisTest} hypoResult={hypoResult} />

          {savedAnalyses.length >= 2 && (
            <SeccionComparadorDeEscenariosPROB016 selectedComp1={selectedComp1} setSelectedComp1={setSelectedComp1} savedAnalyses={savedAnalyses} selectedComp2={selectedComp2} setSelectedComp2={setSelectedComp2} runComparison={runComparison} compareResult={compareResult} />
          )}
        </section>
      </div>
    </div>
  );
}
