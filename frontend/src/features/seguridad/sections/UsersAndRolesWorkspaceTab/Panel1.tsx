import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { Plus, ShieldCheck, UserPlus, Users } from "lucide-react";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";

export function Panel1({ workspaceView, setWorkspaceView, members, catalogRoles, canWrite, loading, saving, roles, setInviteModalOpen, openRoleCreator }: { workspaceView: ReturnType<typeof useUsersAndRolesWorkspaceTab>["workspaceView"]; setWorkspaceView: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setWorkspaceView"]; members: ReturnType<typeof useUsersAndRolesWorkspaceTab>["members"]; catalogRoles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["catalogRoles"]; loading: ReturnType<typeof useUsersAndRolesWorkspaceTab>["loading"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"]; roles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roles"]; setInviteModalOpen: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setInviteModalOpen"]; openRoleCreator: ReturnType<typeof useUsersAndRolesWorkspaceTab>["openRoleCreator"] } & { canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  return (<div className="flex flex-wrap items-center justify-between gap-3 mb-3.5 shrink-0">
    <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1" role="tablist" aria-label="Administración de acceso">
      <button
        type="button"
        role="tab"
        aria-selected={workspaceView === "members"}
        onClick={() => setWorkspaceView("members")}
        className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${workspaceView === "members" ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
      >
        <Users className="h-4 w-4" />
        Usuarios y miembros
        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] text-slate-700">{members.length}</span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={workspaceView === "roles"}
        onClick={() => setWorkspaceView("roles")}
        className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${workspaceView === "roles" ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
      >
        <ShieldCheck className="h-4 w-4" />
        Roles y permisos
        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] text-slate-700">{catalogRoles.length}</span>
      </button>
    </div>
    {workspaceView === "members" && (
      <button
        disabled={!canWrite || loading || saving || roles.length === 0}
        onClick={() => setInviteModalOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
      >
        <UserPlus className="h-4 w-4" />
        Invitar Miembro
      </button>
    )}
    {workspaceView === "roles" && (
      <button
        disabled={!canWrite || loading || saving}
        onClick={() => openRoleCreator()}
        className="inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800"
      >
        <Plus className="h-4 w-4" />
        Crear rol personalizado
      </button>
    )}
  </div>);
}
