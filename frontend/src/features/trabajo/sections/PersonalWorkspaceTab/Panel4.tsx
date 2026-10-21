import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertCircle, Calendar, X } from "lucide-react";

export function Panel4({ activePopover, setActivePopover, quickDueDate, formatQuickDateChip, quickDueTime, setQuickDueDate, setQuickDueTime, applyDateShortcut, isQuickDateInPast }: { activePopover: ReturnType<typeof usePersonalWorkspaceTab>["activePopover"]; setActivePopover: ReturnType<typeof usePersonalWorkspaceTab>["setActivePopover"]; quickDueDate: ReturnType<typeof usePersonalWorkspaceTab>["quickDueDate"]; formatQuickDateChip: ReturnType<typeof usePersonalWorkspaceTab>["formatQuickDateChip"]; quickDueTime: ReturnType<typeof usePersonalWorkspaceTab>["quickDueTime"]; setQuickDueDate: ReturnType<typeof usePersonalWorkspaceTab>["setQuickDueDate"]; setQuickDueTime: ReturnType<typeof usePersonalWorkspaceTab>["setQuickDueTime"]; applyDateShortcut: ReturnType<typeof usePersonalWorkspaceTab>["applyDateShortcut"]; isQuickDateInPast: ReturnType<typeof usePersonalWorkspaceTab>["isQuickDateInPast"] }) {
  return (<div className="relative">
    <div className={`inline-flex items-center rounded-lg border text-xs font-medium transition ${activePopover === "date" ? "border-teal-500 dark:border-teal-500 bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-200 ring-1 ring-teal-400 dark:ring-teal-600" : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700"}`}>
      <button
        type="button"
        aria-label="Seleccionar fecha"
        aria-haspopup="true"
        aria-expanded={activePopover === "date"}
        onClick={() => setActivePopover(prev => prev === "date" ? null : "date")}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${quickDueDate ? "text-teal-700 dark:text-teal-300 font-semibold" : ""
          }`}
      >
        <Calendar className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
        <span>{formatQuickDateChip(quickDueDate, quickDueTime)}</span>
      </button>
      {quickDueDate && (
        <button
          type="button"
          aria-label="Quitar fecha"
          onClick={() => {
            setQuickDueDate("");
            setQuickDueTime("");
          }}
          className="p-1 pr-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>

    {activePopover === "date" && (
      <div className="absolute left-0 top-full mt-1.5 z-40 w-64 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-xl space-y-3">
        <div className="grid grid-cols-2 gap-1">
          <button
            type="button"
            onClick={() => applyDateShortcut("today")}
            className="rounded-lg bg-slate-50 dark:bg-slate-800/60 px-2 py-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-left"
          >
            Hoy
          </button>
          <button
            type="button"
            onClick={() => applyDateShortcut("tomorrow")}
            className="rounded-lg bg-slate-50 dark:bg-slate-800/60 px-2 py-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-left"
          >
            Mañana
          </button>
          <button
            type="button"
            onClick={() => applyDateShortcut("friday")}
            className="rounded-lg bg-slate-50 dark:bg-slate-800/60 px-2 py-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-left"
          >
            Este viernes
          </button>
          <button
            type="button"
            onClick={() => applyDateShortcut("next_week")}
            className="rounded-lg bg-slate-50 dark:bg-slate-800/60 px-2 py-1.5 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-left"
          >
            Próxima semana
          </button>
        </div>

        <div className="space-y-1 pt-1 border-t border-slate-100 dark:border-slate-800">
          <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Fecha y hora opcional
          </span>
          <div className="grid grid-cols-5 gap-1.5">
            <input
              type="date"
              value={quickDueDate}
              onChange={e => setQuickDueDate(e.target.value)}
              className="col-span-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
            />
            <input
              type="time"
              value={quickDueTime}
              onChange={e => setQuickDueTime(e.target.value)}
              className="col-span-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
            />
          </div>
        </div>

        {isQuickDateInPast(quickDueDate, quickDueTime) && (
          <div className="flex items-center gap-1.5 text-[11px] text-amber-600 dark:text-amber-400">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span>La fecha u hora seleccionada ya pasó</span>
          </div>
        )}

        <div className="flex justify-end gap-1.5 pt-1">
          <button
            type="button"
            onClick={() => {
              setQuickDueDate("");
              setQuickDueTime("");
              setActivePopover(null);
            }}
            className="rounded-lg px-2.5 py-1 text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          >
            Limpiar
          </button>
          <button
            type="button"
            onClick={() => setActivePopover(null)}
            className="rounded-lg bg-teal-700 px-3 py-1 text-xs font-semibold text-white hover:bg-teal-800"
          >
            Aceptar
          </button>
        </div>
      </div>
    )}
  </div>);
}
