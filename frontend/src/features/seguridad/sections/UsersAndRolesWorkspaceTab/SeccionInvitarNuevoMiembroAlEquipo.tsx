import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";

export function SeccionInvitarNuevoMiembroAlEquipo({ handleInvite, inviteEmail, setInviteEmail, inviteRole, setInviteRole, roles, setInviteModalOpen, canWrite, saving }: { handleInvite: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleInvite"]; inviteEmail: ReturnType<typeof useUsersAndRolesWorkspaceTab>["inviteEmail"]; setInviteEmail: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setInviteEmail"]; inviteRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["inviteRole"]; setInviteRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setInviteRole"]; roles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roles"]; setInviteModalOpen: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setInviteModalOpen"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"] } & { canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
    <form onSubmit={handleInvite} className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <h3 className="font-bold text-slate-900">Invitar Nuevo Miembro al Equipo</h3>
      <p className="mt-1 text-xs text-slate-500">Se enviará un correo con enlace seguro para activar la cuenta.</p>

      <div className="mt-4 space-y-4">
        <div>
          <label htmlFor="invite-email-input" className="block text-xs font-semibold text-slate-700">Correo Electrónico</label>
          <input
            id="invite-email-input"
            type="email"
            required
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="operador@empresa.com"
            className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="invite-role-select" className="block text-xs font-semibold text-slate-700">Rol Inicial</label>
          <CustomSelect
            id="invite-role-select"
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {roles.map((r) => (
              <option key={r.role} value={r.role}>{r.title}</option>
            ))}
          </CustomSelect>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setInviteModalOpen(false)}
          className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          type="submit" disabled={!canWrite || saving || !inviteRole}
          className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Enviar Invitación
        </button>
      </div>
    </form>
  </div>);
}
