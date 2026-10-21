import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { BookmarkPlus, Copy } from "lucide-react";
import { InfoTooltip } from "../../../../ui/components/InfoTooltip";

export function SeccionDefinicionDeUniversoYEventos({ entityUniverse, setEntityUniverse, period, setPeriod, activeMode, sampleSpace, setSampleSpace, eventACount, setEventACount, eventBCount, setEventBCount, intersectionCount, setIntersectionCount, numberMode, priorA, setPriorA, likelihoodA, setLikelihoodA, evidenceB, setEvidenceB, smoothingEnabled, alphaVal, setAlphaVal, loading, calculateEmpirical, calculateManual, analysisName, setAnalysisName, saveAnalysis, savedAnalyses, duplicateAsSimulation }: { entityUniverse: ReturnType<typeof useProbabilityWorkspaceTab>["entityUniverse"]; setEntityUniverse: ReturnType<typeof useProbabilityWorkspaceTab>["setEntityUniverse"]; period: ReturnType<typeof useProbabilityWorkspaceTab>["period"]; setPeriod: ReturnType<typeof useProbabilityWorkspaceTab>["setPeriod"]; activeMode: ReturnType<typeof useProbabilityWorkspaceTab>["activeMode"]; sampleSpace: ReturnType<typeof useProbabilityWorkspaceTab>["sampleSpace"]; setSampleSpace: ReturnType<typeof useProbabilityWorkspaceTab>["setSampleSpace"]; eventACount: ReturnType<typeof useProbabilityWorkspaceTab>["eventACount"]; setEventACount: ReturnType<typeof useProbabilityWorkspaceTab>["setEventACount"]; eventBCount: ReturnType<typeof useProbabilityWorkspaceTab>["eventBCount"]; setEventBCount: ReturnType<typeof useProbabilityWorkspaceTab>["setEventBCount"]; intersectionCount: ReturnType<typeof useProbabilityWorkspaceTab>["intersectionCount"]; setIntersectionCount: ReturnType<typeof useProbabilityWorkspaceTab>["setIntersectionCount"]; numberMode: ReturnType<typeof useProbabilityWorkspaceTab>["numberMode"]; priorA: ReturnType<typeof useProbabilityWorkspaceTab>["priorA"]; setPriorA: ReturnType<typeof useProbabilityWorkspaceTab>["setPriorA"]; likelihoodA: ReturnType<typeof useProbabilityWorkspaceTab>["likelihoodA"]; setLikelihoodA: ReturnType<typeof useProbabilityWorkspaceTab>["setLikelihoodA"]; evidenceB: ReturnType<typeof useProbabilityWorkspaceTab>["evidenceB"]; setEvidenceB: ReturnType<typeof useProbabilityWorkspaceTab>["setEvidenceB"]; smoothingEnabled: ReturnType<typeof useProbabilityWorkspaceTab>["smoothingEnabled"]; alphaVal: ReturnType<typeof useProbabilityWorkspaceTab>["alphaVal"]; setAlphaVal: ReturnType<typeof useProbabilityWorkspaceTab>["setAlphaVal"]; loading: ReturnType<typeof useProbabilityWorkspaceTab>["loading"]; calculateEmpirical: ReturnType<typeof useProbabilityWorkspaceTab>["calculateEmpirical"]; calculateManual: ReturnType<typeof useProbabilityWorkspaceTab>["calculateManual"]; analysisName: ReturnType<typeof useProbabilityWorkspaceTab>["analysisName"]; setAnalysisName: ReturnType<typeof useProbabilityWorkspaceTab>["setAnalysisName"]; saveAnalysis: ReturnType<typeof useProbabilityWorkspaceTab>["saveAnalysis"]; savedAnalyses: ReturnType<typeof useProbabilityWorkspaceTab>["savedAnalyses"]; duplicateAsSimulation: ReturnType<typeof useProbabilityWorkspaceTab>["duplicateAsSimulation"] }) {
  return (<section className="space-y-6 lg:col-span-5">
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <header className="border-b border-slate-100 pb-4 dark:border-slate-800">
        <div className="flex items-center gap-2"><h2 className="text-base font-semibold text-slate-900 dark:text-white">Definición de Universo y Eventos</h2><InfoTooltip title="Universo y eventos" description="Define la población analizada y las condiciones lógicas de los eventos A y B usadas en todos los cálculos." /></div>
        <p className="mt-1 text-xs text-slate-500">
          Selecciona la entidad base para conteos únicos y las condiciones de A y B.
        </p>
      </header>

      <div className="mt-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="universe-entity" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              Entidad Universo
            </label>
            <CustomSelect
              id="universe-entity"
              value={entityUniverse}
              onChange={(e) => setEntityUniverse(e.target.value as any)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="customers">Clientes Únicos (DISTINCT)</option>
              <option value="sales">Ventas (Transacciones)</option>
            </CustomSelect>
          </div>

          <div>
            <label htmlFor="universe-period" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              Periodo Temporal
            </label>
            <CustomSelect
              id="universe-period"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="7d">Últimos 7 días</option>
              <option value="30d">Últimos 30 días</option>
              <option value="90d">Últimos 90 días</option>
              <option value="all">Todo el historial</option>
            </CustomSelect>
          </div>
        </div>

        {activeMode === "empirical" ? (
          <div className="space-y-4 pt-2">
            <div>
              <label htmlFor="sample-space" className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Tamaño del Universo n(Total)</span>
                <span className="text-slate-400">Población elegible</span>
              </label>
              <input
                id="sample-space"
                type="number"
                min="0"
                value={sampleSpace}
                onChange={(e) => setSampleSpace(Number(e.target.value))}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="event-a" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Recuento Evento A n(A)
                </label>
                <input
                  id="event-a"
                  type="number"
                  min="0"
                  value={eventACount}
                  onChange={(e) => setEventACount(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>
              <div>
                <label htmlFor="event-b" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Recuento Evento B n(B)
                </label>
                <input
                  id="event-b"
                  type="number"
                  min="0"
                  value={eventBCount}
                  onChange={(e) => setEventBCount(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label htmlFor="event-inter" className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Intersección n(A ∩ B)</span>
                <span className="text-slate-400">Cumplen ambas</span>
              </label>
              <input
                id="event-inter"
                type="number"
                min="0"
                value={intersectionCount}
                onChange={(e) => setIntersectionCount(Number(e.target.value))}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4 pt-2">
            <div>
              <label htmlFor="prior-a-input" className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Probabilidad a Priori P(A)</span>
                <span className="text-slate-400">{numberMode === "percentage" ? "%" : "0 - 1"}</span>
              </label>
              <input
                id="prior-a-input"
                type="text"
                value={priorA}
                onChange={(e) => setPriorA(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label htmlFor="likelihood-input" className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Verosimilitud P(B|A)</span>
                <span className="text-slate-400">B dado A</span>
              </label>
              <input
                id="likelihood-input"
                type="text"
                value={likelihoodA}
                onChange={(e) => setLikelihoodA(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label htmlFor="evidence-input" className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300">
                <span>Evidencia Marginal P(B)</span>
                <span className="text-slate-400">P(B) &gt; 0</span>
              </label>
              <input
                id="evidence-input"
                type="text"
                value={evidenceB}
                onChange={(e) => setEvidenceB(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>
        )}

        {smoothingEnabled && (
          <div>
            <label htmlFor="alpha-input" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
              Parámetro Alpha (Regularización)
            </label>
            <input
              id="alpha-input"
              type="text"
              value={alphaVal}
              onChange={(e) => setAlphaVal(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>
        )}

        <div className="pt-2">
          <button
            type="button"
            disabled={loading}
            onClick={activeMode === "empirical" ? calculateEmpirical : calculateManual}
            className="w-full rounded-xl bg-teal-700 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 focus:ring-4 focus:ring-teal-100 disabled:opacity-50"
          >
            {loading ? "Calculando probabilidades…" : "Ejecutar Inferencia de Probabilidades"}
          </button>
        </div>
      </div>
    </article>

    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2"><h3 className="text-sm font-semibold text-slate-900 dark:text-white">Persistencia de Análisis</h3><InfoTooltip title="Persistencia del análisis" description="Guarda parámetros y resultados para reproducir, auditar o comparar este escenario posteriormente." /></div>
          <p className="text-xs text-slate-500">Guarda este escenario para auditoría o simulación.</p>
        </div>
      </header>

      <div className="mt-4 flex gap-2">
        <input
          type="text"
          placeholder="Nombre del análisis (ej. Retención Q3)"
          value={analysisName}
          onChange={(e) => setAnalysisName(e.target.value)}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
        />
        <button
          type="button"
          onClick={saveAnalysis}
          className="flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-teal-700 dark:hover:bg-teal-600"
        >
          <BookmarkPlus className="h-4 w-4" />
          Guardar
        </button>
      </div>

      <div className="mt-5 space-y-2 max-h-56 overflow-y-auto">
        {savedAnalyses.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/60"
          >
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">{item.name}</p>
              <span
                className={`inline-block mt-1 rounded px-2 py-0.5 text-[10px] font-semibold ${item.is_simulation
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  : "bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300"
                  }`}
              >
                {item.is_simulation ? "Simulación Hipotética" : "Dato Observado"}
              </span>
            </div>

            {!item.is_simulation && (
              <button
                type="button"
                onClick={() => duplicateAsSimulation(item.id)}
                className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
              >
                <Copy className="h-3 w-3" />
                Duplicar
              </button>
            )}
          </div>
        ))}
        {savedAnalyses.length === 0 && (
          <p className="text-center py-4 text-xs text-slate-400">Sin análisis guardados en este tenant.</p>
        )}
      </div>
    </article>
  </section>);
}
