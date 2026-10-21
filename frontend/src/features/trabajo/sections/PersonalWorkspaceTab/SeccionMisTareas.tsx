import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertCircle, Calendar, Check, CheckSquare, Pencil, Search, Trash2 } from "lucide-react";
import { PersonalWorkspaceTabProps } from "../../types/PersonalWorkspaceTab";
import { PRIORITY_LABELS } from "../../support/PersonalWorkspaceTab";
import { isDateToday } from "../../support/PersonalWorkspaceTab";
import { isDateOverdue } from "../../support/PersonalWorkspaceTab";
import { formatDisplayDate } from "../../support/PersonalWorkspaceTab";

export function SeccionMisTareas({ tasksSectionRef, tasks, setTaskFilter, taskFilter, pendingTasks, overdueTasks, completedTasks, taskSearch, setTaskSearch, tasksError, loadTasks, currentUserId, tasksLoading, filteredTasks, highlightedTaskId, handleToggleTaskStatus, onOpenResource, setTaskToEdit, setTaskToDelete }: { tasksSectionRef: ReturnType<typeof usePersonalWorkspaceTab>["tasksSectionRef"]; tasks: ReturnType<typeof usePersonalWorkspaceTab>["tasks"]; setTaskFilter: ReturnType<typeof usePersonalWorkspaceTab>["setTaskFilter"]; taskFilter: ReturnType<typeof usePersonalWorkspaceTab>["taskFilter"]; pendingTasks: ReturnType<typeof usePersonalWorkspaceTab>["pendingTasks"]; overdueTasks: ReturnType<typeof usePersonalWorkspaceTab>["overdueTasks"]; completedTasks: ReturnType<typeof usePersonalWorkspaceTab>["completedTasks"]; taskSearch: ReturnType<typeof usePersonalWorkspaceTab>["taskSearch"]; setTaskSearch: ReturnType<typeof usePersonalWorkspaceTab>["setTaskSearch"]; tasksError: ReturnType<typeof usePersonalWorkspaceTab>["tasksError"]; loadTasks: ReturnType<typeof usePersonalWorkspaceTab>["loadTasks"]; currentUserId: ReturnType<typeof usePersonalWorkspaceTab>["currentUserId"]; tasksLoading: ReturnType<typeof usePersonalWorkspaceTab>["tasksLoading"]; filteredTasks: ReturnType<typeof usePersonalWorkspaceTab>["filteredTasks"]; highlightedTaskId: ReturnType<typeof usePersonalWorkspaceTab>["highlightedTaskId"]; handleToggleTaskStatus: ReturnType<typeof usePersonalWorkspaceTab>["handleToggleTaskStatus"]; setTaskToEdit: ReturnType<typeof usePersonalWorkspaceTab>["setTaskToEdit"]; setTaskToDelete: ReturnType<typeof usePersonalWorkspaceTab>["setTaskToDelete"] } & { onOpenResource: PersonalWorkspaceTabProps["onOpenResource"] }) {
  return (<section
    ref={tasksSectionRef}
    id="section-tasks"
    className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-4 flex flex-col justify-between"
  >
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <CheckSquare className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          <h3 className="font-bold text-slate-900 dark:text-slate-100">Mis Tareas</h3>
          <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-semibold tabular-nums text-slate-600 dark:text-slate-400">
            {tasks.length}
          </span>
        </div>

        <div className="flex items-center gap-1 rounded-xl bg-slate-100 dark:bg-slate-800 p-1 text-xs">
          {(["pending", "overdue", "completed", "all"] as const).map(tabKey => (
            <button
              key={tabKey}
              type="button"
              onClick={() => setTaskFilter(tabKey)}
              className={`rounded-lg px-2.5 py-1 font-semibold transition ${taskFilter === tabKey
                ? "bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                }`}
            >
              {tabKey === "pending"
                ? `Pendientes (${pendingTasks.length})`
                : tabKey === "overdue"
                  ? `Vencidas (${overdueTasks.length})`
                  : tabKey === "completed"
                    ? `Completadas (${completedTasks.length})`
                    : `Todas (${tasks.length})`}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
        <input
          type="text"
          placeholder="Buscar tareas por título o nota..."
          value={taskSearch}
          onChange={e => setTaskSearch(e.target.value)}
          className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/70 py-1.5 pl-9 pr-3 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600 focus:bg-white dark:focus:bg-slate-900"
        />
      </div>

      {tasksError && (
        <div className="flex items-center justify-between rounded-xl bg-rose-50 dark:bg-rose-950/40 p-3 text-xs text-rose-800 dark:text-rose-300">
          <span className="flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" /> {tasksError}
          </span>
          <button
            type="button"
            onClick={() => loadTasks(currentUserId, taskSearch)}
            className="font-bold underline hover:text-rose-900 dark:hover:text-rose-100"
          >
            Reintentar
          </button>
        </div>
      )}

      {tasksLoading ? (
        <div className="space-y-2 py-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 w-full animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <CheckSquare className="h-10 w-10 text-slate-300 dark:text-slate-700 stroke-1 mb-2" />
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">
            {taskFilter === "overdue" ? "¡Excelente! No tienes tareas vencidas." : taskFilter === "completed" ? "Aún no has completado tareas." : "No hay tareas registradas en este filtro."}
          </p>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Usa el compositor superior para registrar pendientes rápidos.</p>
        </div>
      ) : (
        <ul className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
          {filteredTasks.map(t => {
            const isDone = t.status === "completed";
            const isOver = !isDone && isDateOverdue(t.due_date);
            const isToday = !isDone && isDateToday(t.due_date);
            const isHighlighted = t.id === highlightedTaskId;

            return (
              <li
                key={t.id}
                className={`group flex items-start justify-between gap-3 rounded-2xl border p-3 transition ${isHighlighted
                  ? "border-teal-500 bg-teal-50/60 dark:bg-teal-950/40 ring-2 ring-teal-500 shadow-md"
                  : isDone
                    ? "border-slate-100 dark:border-slate-800/60 bg-slate-50/60 dark:bg-slate-800/40 opacity-75"
                    : isOver
                      ? "border-rose-200 dark:border-rose-900/60 bg-rose-50/30 dark:bg-rose-950/20 hover:border-rose-300"
                      : isToday
                        ? "border-amber-200 dark:border-amber-900/60 bg-amber-50/20 dark:bg-amber-950/20 hover:border-amber-300"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm"
                  }`}
              >
                <div className="flex items-start gap-2.5 min-w-0 flex-1">
                  <button
                    type="button"
                    onClick={() => handleToggleTaskStatus(t)}
                    title={isDone ? "Marcar como pendiente" : "Completar tarea"}
                    className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition ${isDone
                      ? "border-teal-600 bg-teal-600 text-white"
                      : "border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-teal-500"
                      }`}
                  >
                    {isDone && <Check className="h-3 w-3" />}
                  </button>

                  <div className="min-w-0 space-y-1">
                    <p className={`text-xs font-semibold ${isDone ? "line-through text-slate-400 dark:text-slate-500" : "text-slate-900 dark:text-slate-100"}`}>
                      {t.title}
                    </p>
                    {t.description && (
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">{t.description}</p>
                    )}
                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                      <span
                        className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-semibold border ${t.priority === "high" || t.priority === "urgent"
                          ? "bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800"
                          : t.priority === "normal"
                            ? "bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                          }`}
                      >
                        {PRIORITY_LABELS[t.priority] || "Media"}
                      </span>

                      <span
                        className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium border ${isOver
                          ? "bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-200 border-rose-300 dark:border-rose-700 font-semibold"
                          : isToday
                            ? "bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-200 border-amber-300 dark:border-amber-700 font-semibold"
                            : "bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700"
                          }`}
                      >
                        <Calendar className="h-2.5 w-2.5" />
                        {formatDisplayDate(t.due_date)}
                      </span>

                      {t.resource_name && (
                        <button type="button" disabled={!t.resource_id || !onOpenResource} onClick={() => t.resource_type && t.resource_id && onOpenResource?.(t.resource_type, t.resource_id)} className="inline-flex items-center gap-1 rounded-md bg-teal-50 dark:bg-teal-950/60 px-1.5 py-0.5 text-[10px] font-medium text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 disabled:cursor-default">
                          {{ order: "Pedido", customer: "Cliente", product: "Producto", sale: "Venta" }[t.resource_type || "customer"] || "Registro"}: {t.resource_name}
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition shrink-0">
                  <button
                    type="button"
                    onClick={() => setTaskToEdit(t)}
                    title="Editar tarea"
                    className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-200"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setTaskToDelete(t)}
                    title="Eliminar tarea"
                    className="rounded-lg p-1 text-slate-400 hover:bg-rose-50 dark:hover:bg-rose-950/60 hover:text-rose-600 dark:hover:text-rose-400"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  </section>);
}
