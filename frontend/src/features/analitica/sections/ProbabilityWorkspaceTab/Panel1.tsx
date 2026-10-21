import type { useProbabilityWorkspaceTab } from "../../hooks/useProbabilityWorkspaceTab";


export function Panel1({ setActiveMode, activeMode, setNumberMode, numberMode, smoothingEnabled, setSmoothingEnabled, alphaVal }: { setActiveMode: ReturnType<typeof useProbabilityWorkspaceTab>["setActiveMode"]; activeMode: ReturnType<typeof useProbabilityWorkspaceTab>["activeMode"]; setNumberMode: ReturnType<typeof useProbabilityWorkspaceTab>["setNumberMode"]; numberMode: ReturnType<typeof useProbabilityWorkspaceTab>["numberMode"]; smoothingEnabled: ReturnType<typeof useProbabilityWorkspaceTab>["smoothingEnabled"]; setSmoothingEnabled: ReturnType<typeof useProbabilityWorkspaceTab>["setSmoothingEnabled"]; alphaVal: ReturnType<typeof useProbabilityWorkspaceTab>["alphaVal"] }) {
  return (<div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => setActiveMode("empirical")}
        className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${activeMode === "empirical"
          ? "bg-teal-700 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          }`}
      >
        Modo Empírico (Conteos Directos)
      </button>
      <button
        type="button"
        onClick={() => setActiveMode("manual")}
        className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${activeMode === "manual"
          ? "bg-teal-700 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          }`}
      >
        Modo Manual (Parámetros Directos)
      </button>
    </div>

    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-800">
        <button
          type="button"
          onClick={() => setNumberMode("proportion")}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${numberMode === "proportion"
            ? "bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white"
            : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
        >
          Proporción [0, 1]
        </button>
        <button
          type="button"
          onClick={() => setNumberMode("percentage")}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${numberMode === "percentage"
            ? "bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white"
            : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
        >
          Porcentaje [0, 100 %]
        </button>
      </div>

      <label className="flex items-center gap-2 text-xs font-medium text-slate-700 dark:text-slate-300">
        <input
          type="checkbox"
          checked={smoothingEnabled}
          onChange={(e) => setSmoothingEnabled(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
        />
        Suavizado de Laplace (Alpha={alphaVal})
      </label>
    </div>
  </div>);
}
