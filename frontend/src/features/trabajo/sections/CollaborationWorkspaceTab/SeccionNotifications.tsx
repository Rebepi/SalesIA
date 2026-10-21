import type { useCollaborationWorkspaceTab } from "../../hooks/useCollaborationWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";

export function SeccionNotifications({ priorityFilter, setPriorityFilter, notifications, markRead }: { priorityFilter: ReturnType<typeof useCollaborationWorkspaceTab>["priorityFilter"]; setPriorityFilter: ReturnType<typeof useCollaborationWorkspaceTab>["setPriorityFilter"]; notifications: ReturnType<typeof useCollaborationWorkspaceTab>["notifications"]; markRead: ReturnType<typeof useCollaborationWorkspaceTab>["markRead"] }) {
  return (<div className="space-y-4">
    <div className="flex items-center justify-between gap-4">
      <h2 className="text-lg font-semibold text-slate-900">Bandeja de notificaciones y alertas</h2>
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">Filtrar prioridad:</span>
        <CustomSelect
          value={priorityFilter}
          onChange={e => setPriorityFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 outline-none"
        >
          <option value="">Todas</option>
          <option value="high">Alta</option>
          <option value="normal">Normal</option>
          <option value="low">Baja</option>
        </CustomSelect>
      </div>
    </div>
    {notifications.length === 0 ? (
      <p className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">No hay notificaciones registradas.</p>
    ) : (
      <div className="grid gap-3">
        {notifications.map(n => (
          <div key={n.id} className={`flex items-start justify-between gap-4 rounded-2xl border p-5 transition ${n.read ? "border-slate-200 bg-white" : "border-teal-200 bg-teal-50/50 shadow-sm"}`}>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${n.priority === "high" ? "bg-red-100 text-red-800" : "bg-slate-100 text-slate-700"}`}>{n.priority.toUpperCase()}</span>
                <span className="text-xs text-slate-400">{n.category}</span>
                <h3 className="font-semibold text-slate-900">{n.title}</h3>
              </div>
              <p className="text-sm text-slate-600">{n.message}</p>
              <p className="text-xs text-slate-400">{new Date(n.created_at).toLocaleString()}</p>
            </div>
            {!n.read && (
              <button
                onClick={() => markRead(n.id)}
                className="rounded-lg border border-teal-300 bg-white px-3 py-1.5 text-xs font-semibold text-teal-800 transition hover:bg-teal-100"
              >
                Marcar leída
              </button>
            )}
          </div>
        ))}
      </div>
    )}
  </div>);
}
