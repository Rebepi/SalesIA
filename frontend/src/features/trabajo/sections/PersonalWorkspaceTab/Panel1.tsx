import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertTriangle, CheckSquare, Clock, TrendingUp } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { formatMoney } from "../../support/PersonalWorkspaceTab";

export function Panel1({ setTaskFilter, scrollToSection, tasksSectionRef, pendingTasks, overdueTasks, ordersSectionRef, orders, quotaSectionRef, salesProgress, baseCurrency }: { setTaskFilter: ReturnType<typeof usePersonalWorkspaceTab>["setTaskFilter"]; scrollToSection: ReturnType<typeof usePersonalWorkspaceTab>["scrollToSection"]; tasksSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["tasksSectionRef"]; pendingTasks: ReturnType<typeof usePersonalWorkspaceTab>["pendingTasks"]; overdueTasks: ReturnType<typeof usePersonalWorkspaceTab>["overdueTasks"]; ordersSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["ordersSectionRef"]; orders: ReturnType<typeof usePersonalWorkspaceTab>["orders"]; quotaSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["quotaSectionRef"]; salesProgress: ReturnType<typeof usePersonalWorkspaceTab>["salesProgress"] } & { baseCurrency: NonNullable<PersonalWorkspaceTabProps["baseCurrency"]> }) {
  return (<section aria-label="Resumen de indicadores clave" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
    <button
      type="button"
      onClick={() => { setTaskFilter("pending"); scrollToSection(tasksSectionRef); }}
      className="group flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-left shadow-sm transition hover:border-teal-400 dark:hover:border-teal-600 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Tareas Pendientes</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 group-hover:scale-110 transition">
          <CheckSquare className="h-4 w-4" />
        </span>
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">{pendingTasks.length}</p>
        <p className="text-[11px] text-slate-400">
          {overdueTasks.length > 0 ? (
            <span className="font-semibold text-rose-600 dark:text-rose-400">{overdueTasks.length} vencidas</span>
          ) : (
            "Al día"
          )}
        </p>
      </div>
    </button>

    <button
      type="button"
      onClick={() => { setTaskFilter("overdue"); scrollToSection(tasksSectionRef); }}
      className="group flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-left shadow-sm transition hover:border-rose-400 dark:hover:border-rose-600 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Tareas Vencidas</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 group-hover:scale-110 transition">
          <AlertTriangle className="h-4 w-4" />
        </span>
      </div>
      <div className="mt-3">
        <p className={`text-2xl font-bold tabular-nums ${overdueTasks.length > 0 ? "text-rose-600 dark:text-rose-400" : "text-slate-900 dark:text-slate-100"}`}>
          {overdueTasks.length}
        </p>
        <p className="text-[11px] text-slate-400">Requieren atención</p>
      </div>
    </button>

    <button
      type="button"
      onClick={() => scrollToSection(ordersSectionRef)}
      className="group flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-left shadow-sm transition hover:border-sky-400 dark:hover:border-sky-600 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Pedidos en Curso</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 group-hover:scale-110 transition">
          <Clock className="h-4 w-4" />
        </span>
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">{orders.length}</p>
        <p className="text-[11px] text-slate-400">Activos en seguimiento</p>
      </div>
    </button>

    <button
      type="button"
      onClick={() => scrollToSection(quotaSectionRef)}
      className="group flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-left shadow-sm transition hover:border-emerald-400 dark:hover:border-emerald-600 hover:shadow-md"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Avance de Meta</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 group-hover:scale-110 transition">
          <TrendingUp className="h-4 w-4" />
        </span>
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
          {salesProgress?.attainment !== null && salesProgress?.attainment !== undefined ? `${Math.round(salesProgress.attainment)}%` : "—"}
        </p>
        <p className="text-[11px] text-slate-400">
          {salesProgress?.hasQuota ? formatMoney(salesProgress.currentSales, baseCurrency) : "Sin cuota activa"}
        </p>
      </div>
    </button>
  </section>);
}
