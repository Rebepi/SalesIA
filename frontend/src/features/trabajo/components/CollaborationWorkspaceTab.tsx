import { Panel1 } from "../sections/CollaborationWorkspaceTab/Panel1";
import { SeccionNotifications } from "../sections/CollaborationWorkspaceTab/SeccionNotifications";
import { SeccionTareas } from "../sections/CollaborationWorkspaceTab/SeccionTareas";
import { useCollaborationWorkspaceTab } from "../hooks/useCollaborationWorkspaceTab";
import { Plus } from "lucide-react";
import { TaskPlanningBoard } from "./TaskPlanningBoard";

export function CollaborationWorkspaceTab({ canApprove = false }: { canApprove?: boolean }) {
  const { subTab, setSubTab, notifications, unreadCount, priorityFilter, setPriorityFilter, preferences, tasks, approvals, savedViews, helpArticles, newTaskTitle, setNewTaskTitle, newViewName, setNewViewName, loading, toast, loadNotifications, loadTasks, loadApprovals, loadViews, loadHelp, markRead, togglePreference, createTask, completeTask, decideApproval, createView } = useCollaborationWorkspaceTab({ canApprove });
  return (
    <div className="space-y-6">
      <Panel1 setSubTab={setSubTab} subTab={subTab} unreadCount={unreadCount} loadNotifications={loadNotifications} loadTasks={loadTasks} loadApprovals={loadApprovals} loadViews={loadViews} loadHelp={loadHelp} loading={loading} />

      {subTab === "notifications" && (
        <SeccionNotifications priorityFilter={priorityFilter} setPriorityFilter={setPriorityFilter} notifications={notifications} markRead={markRead} />
      )}

      {subTab === "preferences" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Canales y categorías de notificación</h2>
            <p className="mt-1 text-sm text-slate-500">Configura qué avisos recibir por cada canal. Los avisos de seguridad son de cumplimiento obligatorio.</p>
            <div className="mt-6 divide-y divide-slate-100">
              {preferences.map(p => (
                <div key={`${p.category}-${p.channel}`} className="flex items-center justify-between py-4">
                  <div>
                    <h3 className="font-medium text-slate-900 capitalize">{p.category} ({p.channel === "in_app" ? "En la app" : "Correo electrónico"})</h3>
                    {p.is_mandatory && <p className="text-xs text-red-600 font-medium">Requisito obligatorio de seguridad (no desactivable)</p>}
                  </div>
                  <button
                    onClick={() => togglePreference(p)}
                    disabled={p.is_mandatory}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${p.enabled ? "bg-teal-600" : "bg-slate-300"} ${p.is_mandatory ? "opacity-60 cursor-not-allowed" : "cursor-pointer"}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${p.enabled ? "translate-x-6" : "translate-x-1"}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {subTab === "tasks" && (
        <><SeccionTareas newTaskTitle={newTaskTitle} setNewTaskTitle={setNewTaskTitle} createTask={createTask} tasks={tasks} completeTask={completeTask} /><TaskPlanningBoard /></>
      )}

      {subTab === "approvals" && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Bandeja de aprobaciones y controles</h2>
          <div className="grid gap-3">
            {approvals.map(a => (
              <div key={a.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div>
                  <span className="text-xs font-semibold uppercase text-slate-400">Política: {a.policy_name}</span>
                  <h3 className="font-semibold text-slate-900">Recurso: {a.resource_type} (Versión doc: {a.document_version})</h3>
                  <p className="text-xs text-slate-500">Estado: {a.status}</p>
                </div>
                {a.status === "pending" && canApprove && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => decideApproval(a.id, "approved", a.document_version)}
                      className="rounded-lg bg-teal-700 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-teal-800"
                    >
                      Aprobar
                    </button>
                    <button
                      onClick={() => decideApproval(a.id, "rejected", a.document_version)}
                      className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-50"
                    >
                      Rechazar
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === "views" && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              value={newViewName}
              onChange={e => setNewViewName(e.target.value)}
              placeholder="Nombre de vista guardada…"
              className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none focus:ring-4 focus:ring-teal-100"
            />
            <button
              onClick={createView}
              className="inline-flex items-center gap-2 rounded-xl bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800"
            >
              <Plus className="h-4 w-4" />
              Guardar vista
            </button>
          </div>
          <div className="grid gap-3">
            {savedViews.map(v => (
              <div key={v.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div>
                  <h3 className="font-semibold text-slate-900">{v.name}</h3>
                  <p className="text-xs text-slate-500">Esquema v{v.schema_version} {v.is_migrated && <span className="text-teal-600 font-medium">· Migrada automáticamente</span>}</p>
                </div>
                <button
                  onClick={() => toast.info("Vista aplicada", `Configuración de ${v.name} cargada.`)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Aplicar filtros
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === "help" && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Guías operativas y ayuda contextual</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {helpArticles.map((art, idx) => (
              <div key={idx} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase text-slate-600">{art.screen}</span>
                <h3 className="mt-3 font-semibold text-slate-900">{art.title}</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">{art.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
