import { useState } from "react";
import { UserHandoverDialog } from "./UserHandoverDialog";
import type { MemberItem } from "../types/UsersAndRolesWorkspaceTab";
import { Panel1 } from "../sections/UsersAndRolesWorkspaceTab/Panel1";
import { SeccionMembers } from "../sections/UsersAndRolesWorkspaceTab/SeccionMembers";
import { SeccionRoles } from "../sections/UsersAndRolesWorkspaceTab/SeccionRoles";
import { SeccionEditorDeRolesYPermisos } from "../sections/UsersAndRolesWorkspaceTab/SeccionEditorDeRolesYPermisos";
import { SeccionInvitarNuevoMiembroAlEquipo } from "../sections/UsersAndRolesWorkspaceTab/SeccionInvitarNuevoMiembroAlEquipo";
import { SeccionCrearRolPersonalizado } from "../sections/UsersAndRolesWorkspaceTab/SeccionCrearRolPersonalizado";
export type { MemberItem } from "../types/UsersAndRolesWorkspaceTab";
export type { UsersAndRolesWorkspaceTabProps } from "../types/UsersAndRolesWorkspaceTab";
import { useUsersAndRolesWorkspaceTab } from "../hooks/useUsersAndRolesWorkspaceTab";
import { Trash2 } from "lucide-react";
import { CustomRoleDialog } from "./CustomRoleDialog";
import { UsersAndRolesWorkspaceTabProps } from "../types/UsersAndRolesWorkspaceTab";

export function UsersAndRolesWorkspaceTab({ canWrite = true, currentUserRole = "company_admin" }: UsersAndRolesWorkspaceTabProps) {
  const { ConfirmDialogNode, members, roles, allPermissions, workspaceView, setWorkspaceView, loading, loadError, selectedMember, setSelectedMember, targetRole, setTargetRole, escalationError, setEscalationError, inviteModalOpen, setInviteModalOpen, inviteEmail, setInviteEmail, inviteRole, setInviteRole, cancellingInvitation, setCancellingInvitation, managedRole, setManagedRole, memberSecurity, securityError, setRevision, roleModalOpen, setRoleModalOpen, roleKey, setRoleKey, roleTitle, setRoleTitle, roleDescription, setRoleDescription, selectedPermissions, setSelectedPermissions, permissionSearch, setPermissionSearch, roleDisplay, rolePage, setRolePage, rolePageSize, setRolePageSize, toast, saving, handleOpenEditor, handleSaveRole, handleInvite, handleToggleActive, handleResendInvitation, handleCancelInvitation, permissionGroups, catalogRoles, filteredRoles, roleTotalPages, visibleRoles, roleRangeStart, roleRangeEnd, roleKeyFromTitle, openRoleCreator, togglePermission, handleCreateRole } = useUsersAndRolesWorkspaceTab({ canWrite, currentUserRole });
  const [handoverMember, setHandoverMember] = useState<MemberItem | null>(null);
  async function toggleMember(member: MemberItem) { if (member.is_active) { setSelectedMember(null); setHandoverMember(member); } else await handleToggleActive(member); }
  return (
    <div id="scr-045-users-roles-workspace" data-testid="scr-045-users-roles-workspace" className="flex flex-col flex-1 min-h-0 h-full w-full">
      <h1 className="sr-only">Usuarios, Roles y Control de Acceso (RBAC)</h1>

      <Panel1 workspaceView={workspaceView} setWorkspaceView={setWorkspaceView} members={members} catalogRoles={catalogRoles} canWrite={canWrite} loading={loading} saving={saving} roles={roles} setInviteModalOpen={setInviteModalOpen} openRoleCreator={openRoleCreator} />

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Cargando miembros y catálogo de roles...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}

      {workspaceView === "members" && (
        <SeccionMembers members={members} canWrite={canWrite} saving={saving} handleResendInvitation={handleResendInvitation} setCancellingInvitation={setCancellingInvitation} handleOpenEditor={handleOpenEditor} handleToggleActive={toggleMember} />
      )}

      {workspaceView === "roles" && (
        <SeccionRoles visibleRoles={visibleRoles} roleDisplay={roleDisplay} canWrite={canWrite} saving={saving} setManagedRole={setManagedRole} openRoleCreator={openRoleCreator} roleRangeStart={roleRangeStart} roleRangeEnd={roleRangeEnd} filteredRoles={filteredRoles} rolePageSize={rolePageSize} setRolePageSize={setRolePageSize} setRolePage={setRolePage} rolePage={rolePage} roleTotalPages={roleTotalPages} />
      )}

      {managedRole && <CustomRoleDialog role={managedRole} roles={roles} availablePermissions={allPermissions} onClose={() => setManagedRole(null)} onSaved={() => { setManagedRole(null); setRevision(value => value + 1); toast.success("Rol actualizado", "Los cambios se aplicaron a las membresías afectadas."); }} />}
      {selectedMember && (
        <SeccionEditorDeRolesYPermisos selectedMember={selectedMember} setSelectedMember={setSelectedMember} escalationError={escalationError} memberSecurity={memberSecurity} securityError={securityError} targetRole={targetRole} setTargetRole={setTargetRole} setEscalationError={setEscalationError} roles={roles} currentUserRole={currentUserRole} canWrite={canWrite} saving={saving} handleSaveRole={handleSaveRole} />
      )}

      {inviteModalOpen && (
        <SeccionInvitarNuevoMiembroAlEquipo handleInvite={handleInvite} inviteEmail={inviteEmail} setInviteEmail={setInviteEmail} inviteRole={inviteRole} setInviteRole={setInviteRole} roles={roles} setInviteModalOpen={setInviteModalOpen} canWrite={canWrite} saving={saving} />
      )}

      {roleModalOpen && (
        <SeccionCrearRolPersonalizado handleCreateRole={handleCreateRole} setRoleModalOpen={setRoleModalOpen} roleTitle={roleTitle} roleKeyFromTitle={roleKeyFromTitle} setRoleTitle={setRoleTitle} roleKey={roleKey} setRoleKey={setRoleKey} roleDescription={roleDescription} setRoleDescription={setRoleDescription} selectedPermissions={selectedPermissions} allPermissions={allPermissions} permissionSearch={permissionSearch} setPermissionSearch={setPermissionSearch} permissionGroups={permissionGroups} setSelectedPermissions={setSelectedPermissions} togglePermission={togglePermission} canWrite={canWrite} saving={saving} />
      )}

      {cancellingInvitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true" aria-labelledby="cancel-invitation-title">
          <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-50 text-rose-700">
              <Trash2 className="h-5 w-5" />
            </div>
            <h3 id="cancel-invitation-title" className="mt-4 text-lg font-bold text-slate-900">Cancelar invitación pendiente</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              El enlace enviado a <strong className="text-slate-900">{cancellingInvitation.email}</strong> dejará de funcionar y el usuario provisional se retirará de la lista.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                disabled={saving}
                onClick={() => setCancellingInvitation(null)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              >
                Conservar invitación
              </button>
              <button
                type="button"
                disabled={!canWrite || saving}
                onClick={handleCancelInvitation}
                className="rounded-xl bg-rose-700 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-800"
              >
                {saving ? "Cancelando..." : "Cancelar invitación"}
              </button>
            </div>
          </div>
        </div>
      )}
      {handoverMember && <UserHandoverDialog member={handoverMember} onClose={() => setHandoverMember(null)} onChanged={() => setRevision(value => value + 1)} />}
      {ConfirmDialogNode}
    </div>
  );
}
