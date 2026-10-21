import type { useCollaborationWorkspaceTab } from "../../hooks/useCollaborationWorkspaceTab";
import { Plus } from "lucide-react";

export function SeccionTareas({ newTaskTitle, setNewTaskTitle, createTask, tasks, completeTask }: { newTaskTitle: ReturnType<typeof useCollaborationWorkspaceTab>["newTaskTitle"]; setNewTaskTitle: ReturnType<typeof useCollaborationWorkspaceTab>["setNewTaskTitle"]; createTask: ReturnType<typeof useCollaborationWorkspaceTab>["createTask"]; tasks: ReturnType<typeof useCollaborationWorkspaceTab>["tasks"]; completeTask: ReturnType<typeof useCollaborationWorkspaceTab>["completeTask"] }) {
  return (<div className="space-y-4">
    <div className="flex gap-2">
      <input
        value={newTaskTitle}
        onChange={e => setNewTaskTitle(e.target.value)}
        placeholder="Nueva tarea de seguimiento comercial…"
        className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none focus:ring-4 focus:ring-teal-100"
      />
      <button
        onClick={createTask}
        className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800"
      >
        <Plus className="h-4 w-4" />
        Crear tarea
      </button>
    </div>
    <div className="grid gap-3">
      {tasks.map(t => (
        <div key={t.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <div className="flex items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${t.status === "completed" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{t.status.toUpperCase()}</span>
              <h3 className="font-semibold text-slate-900">{t.title}</h3>
            </div>
            {t.inactive_assignee_warning && <p className="mt-1 text-xs text-amber-600">Alerta: La membresía asignada se encuentra inactiva.</p>}
          </div>
          {t.status !== "completed" && (
            <button
              onClick={() => completeTask(t.id)}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Completar
            </button>
          )}
        </div>
      ))}
    </div>
  </div>);
}
