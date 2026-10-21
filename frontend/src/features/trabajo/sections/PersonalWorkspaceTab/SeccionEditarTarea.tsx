import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";

export function SeccionEditarTarea({ setTaskToEdit, handleSaveEditTask, taskToEdit, editSaving }: { setTaskToEdit: ReturnType<typeof usePersonalWorkspaceTab>["setTaskToEdit"]; handleSaveEditTask: ReturnType<typeof usePersonalWorkspaceTab>["handleSaveEditTask"]; taskToEdit: NonNullable<ReturnType<typeof usePersonalWorkspaceTab>["taskToEdit"]>; editSaving: ReturnType<typeof usePersonalWorkspaceTab>["editSaving"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" onMouseDown={e => { if (e.target === e.currentTarget) setTaskToEdit(null); }}>
    <div className="w-full max-w-md rounded-3xl bg-white dark:bg-slate-900 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <h3 className="font-bold text-slate-900 dark:text-slate-100">Editar Tarea</h3>
        <button
          type="button"
          onClick={() => setTaskToEdit(null)}
          className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSaveEditTask} className="space-y-3">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Título</label>
          <input
            type="text"
            required
            value={taskToEdit.title}
            onChange={e => setTaskToEdit({ ...taskToEdit, title: e.target.value })}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Descripción</label>
          <textarea
            rows={2}
            value={taskToEdit.description || ""}
            onChange={e => setTaskToEdit({ ...taskToEdit, description: e.target.value })}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-teal-600"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Prioridad</label>
            <CustomSelect
              value={taskToEdit.priority}
              onChange={e => setTaskToEdit({ ...taskToEdit, priority: e.target.value as "low" | "normal" | "high" })}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 text-xs text-slate-700 dark:text-slate-300 outline-none focus:border-teal-600"
            >
              <option value="low">Baja</option>
              <option value="normal">Media</option>
              <option value="high">Alta</option>
              <option value="urgent">Urgente</option>
            </CustomSelect>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Fecha límite</label>
            <input
              type="date"
              value={taskToEdit.due_date ? taskToEdit.due_date.slice(0, 10) : ""}
              onChange={e => setTaskToEdit({ ...taskToEdit, due_date: e.target.value ? e.target.value : null })}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 text-xs text-slate-700 dark:text-slate-300 outline-none focus:border-teal-600"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setTaskToEdit(null)}
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={editSaving}
            className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
          >
            {editSaving ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      </form>
    </div>
  </div>);
}
