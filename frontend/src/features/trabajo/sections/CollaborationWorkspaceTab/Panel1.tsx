import type { useCollaborationWorkspaceTab } from "../../hooks/useCollaborationWorkspaceTab";
import { Bell, CheckCircle2, FileText, HelpCircle, ListFilter, RefreshCw, UserCheck } from "lucide-react";

export function Panel1({ setSubTab, subTab, unreadCount, loadNotifications, loadTasks, loadApprovals, loadViews, loadHelp, loading }: { setSubTab: ReturnType<typeof useCollaborationWorkspaceTab>["setSubTab"]; subTab: ReturnType<typeof useCollaborationWorkspaceTab>["subTab"]; unreadCount: ReturnType<typeof useCollaborationWorkspaceTab>["unreadCount"]; loadNotifications: ReturnType<typeof useCollaborationWorkspaceTab>["loadNotifications"]; loadTasks: ReturnType<typeof useCollaborationWorkspaceTab>["loadTasks"]; loadApprovals: ReturnType<typeof useCollaborationWorkspaceTab>["loadApprovals"]; loadViews: ReturnType<typeof useCollaborationWorkspaceTab>["loadViews"]; loadHelp: ReturnType<typeof useCollaborationWorkspaceTab>["loadHelp"]; loading: ReturnType<typeof useCollaborationWorkspaceTab>["loading"] }) {
  return (<div className="workspace-toolbar-card flex flex-wrap items-center justify-between gap-4">
    <div className="flex gap-2">
      <button
        onClick={() => setSubTab("notifications")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "notifications" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <Bell className="h-4 w-4" />
        Notificaciones
        {unreadCount > 0 && <span className="ml-1 rounded-full bg-amber-400 px-2 py-0.5 text-xs font-bold text-slate-900">{unreadCount}</span>}
      </button>
      <button
        onClick={() => setSubTab("tasks")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "tasks" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <CheckCircle2 className="h-4 w-4" />
        Tareas
      </button>
      <button
        onClick={() => setSubTab("approvals")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "approvals" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <UserCheck className="h-4 w-4" />
        Aprobaciones
      </button>
      <button
        onClick={() => setSubTab("preferences")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "preferences" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <ListFilter className="h-4 w-4" />
        Preferencias
      </button>
      <button
        onClick={() => setSubTab("views")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "views" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <FileText className="h-4 w-4" />
        Vistas guardadas
      </button>
      <button
        onClick={() => setSubTab("help")}
        className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${subTab === "help" ? "bg-teal-700 text-white shadow-sm" : "bg-white text-slate-700 hover:bg-slate-100"}`}
      >
        <HelpCircle className="h-4 w-4" />
        Ayuda contextual
      </button>
    </div>
    <button
      onClick={() => {
        if (subTab === "notifications") loadNotifications();
        else if (subTab === "tasks") loadTasks();
        else if (subTab === "approvals") loadApprovals();
        else if (subTab === "views") loadViews();
        else if (subTab === "help") loadHelp();
      }}
      className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50"
    >
      <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-teal-600" : ""}`} />
      Actualizar
    </button>
  </div>);
}
