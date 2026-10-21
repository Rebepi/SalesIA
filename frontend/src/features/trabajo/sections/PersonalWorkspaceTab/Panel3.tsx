import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { Check } from "lucide-react";
import { PRIORITY_LABELS } from "../../support/PersonalWorkspaceTab";
import { PRIORITY_COLORS } from "../../support/PersonalWorkspaceTab";

export function Panel3({ quickPriority, activePopover, setActivePopover, setQuickPriority }: { quickPriority: ReturnType<typeof usePersonalWorkspaceTab>["quickPriority"]; activePopover: ReturnType<typeof usePersonalWorkspaceTab>["activePopover"]; setActivePopover: ReturnType<typeof usePersonalWorkspaceTab>["setActivePopover"]; setQuickPriority: ReturnType<typeof usePersonalWorkspaceTab>["setQuickPriority"] }) {
  return (<div className="relative">
    <button
      type="button"
      aria-label={`Prioridad: ${PRIORITY_LABELS[quickPriority]}`}
      aria-haspopup="true"
      aria-expanded={activePopover === "priority"}
      onClick={() => setActivePopover(prev => prev === "priority" ? null : "priority")}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition ${activePopover === "priority"
        ? "border-teal-500 dark:border-teal-500 bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-200 ring-1 ring-teal-400 dark:ring-teal-600"
        : quickPriority !== "normal"
          ? "border-teal-300 dark:border-teal-700 bg-teal-50/50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-200"
          : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"
        }`}
    >
      <span className={`h-2 w-2 rounded-full ${PRIORITY_COLORS[quickPriority]}`} />
      <span>{PRIORITY_LABELS[quickPriority]}</span>
    </button>

    {activePopover === "priority" && (
      <div className="absolute left-0 top-full mt-1.5 z-40 w-36 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1 shadow-xl space-y-0.5">
        {(["low", "normal", "high", "urgent"] as const).map(pKey => (
          <button
            key={pKey}
            type="button"
            onClick={() => {
              setQuickPriority(pKey);
              setActivePopover(null);
            }}
            className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium text-left transition ${quickPriority === pKey
              ? "bg-slate-100 dark:bg-slate-800 text-teal-700 dark:text-teal-400"
              : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60"
              }`}
          >
            <span className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${PRIORITY_COLORS[pKey]}`} />
              {PRIORITY_LABELS[pKey]}
            </span>
            {quickPriority === pKey && <Check className="h-3 w-3 text-teal-600 dark:text-teal-400" />}
          </button>
        ))}
      </div>
    )}
  </div>);
}
