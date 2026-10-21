import type { usePersonalWorkspaceTab } from "../../hooks/usePersonalWorkspaceTab";
import { AlertTriangle } from "lucide-react";

export function SeccionEliminarActividad({ setTaskToDelete, taskToDelete, handleConfirmDeleteTask, deleteSaving }: { setTaskToDelete: ReturnType<typeof usePersonalWorkspaceTab>["setTaskToDelete"]; taskToDelete: NonNullable<ReturnType<typeof usePersonalWorkspaceTab>["taskToDelete"]>; handleConfirmDeleteTask: ReturnType<typeof usePersonalWorkspaceTab>["handleConfirmDeleteTask"]; deleteSaving: ReturnType<typeof usePersonalWorkspaceTab>["deleteSaving"] }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" onMouseDown={e => { if (e.target === e.currentTarget) setTaskToDelete(null); }}>
    <div className="w-full max-w-sm rounded-3xl bg-white dark:bg-slate-900 p-6 shadow-xl space-y-4">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <div>
          <h3 className="font-bold text-slate-900 dark:text-slate-100">¿Eliminar actividad?</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Esta acción no se puede deshacer.</p>
        </div>
      </div>

      <p className="rounded-xl bg-slate-50 dark:bg-slate-800/60 p-3 text-xs font-medium text-slate-800 dark:text-slate-200 border border-slate-100 dark:border-slate-800">
        {taskToDelete.title}
      </p>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={() => setTaskToDelete(null)}
          className="rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={handleConfirmDeleteTask}
          disabled={deleteSaving}
          className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
        >
          {deleteSaving ? "Eliminando..." : "Sí, eliminar"}
        </button>
      </div>
    </div>
  </div>);
}
