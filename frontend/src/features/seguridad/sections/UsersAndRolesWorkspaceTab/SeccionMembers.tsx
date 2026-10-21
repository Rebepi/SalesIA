import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { Pencil as ActionPencil, Power as ActionPower } from "lucide-react";
import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { PaginatedTable } from "../../../../ui/components/PaginatedTable";
import { RefreshCw, Trash2 } from "lucide-react";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";

export function SeccionMembers({ members, canWrite, saving, handleResendInvitation, setCancellingInvitation, handleOpenEditor, handleToggleActive }: { members: ReturnType<typeof useUsersAndRolesWorkspaceTab>["members"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"]; handleResendInvitation: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleResendInvitation"]; setCancellingInvitation: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setCancellingInvitation"]; handleOpenEditor: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleOpenEditor"]; handleToggleActive: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleToggleActive"] } & { canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  return (<div className="pagination-shell flex flex-col flex-1 min-h-0">
    <PaginatedTable className="w-full text-left text-sm">
      <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500">
        <tr>
          <th scope="col" className="px-4 py-3">Nombre & Correo</th>
          <th scope="col" className="px-4 py-3">Rol Empresarial</th>
          <th scope="col" className="px-4 py-3">Estado</th>
          <th scope="col" className="px-4 py-3">Sedes Autorizadas</th>
          <th scope="col" className="px-4 py-3 text-right">Acciones</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {members.map((m) => (
          <tr key={m.id} className="hover:bg-slate-50">
            <td className="px-4 py-3">
              <p className="font-semibold text-slate-900">{m.name}</p>
              <p className="text-xs text-slate-500 font-mono">{m.email}</p>
            </td>
            <td className="px-4 py-3">
              <span className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-bold text-teal-800 border border-teal-200">
                {m.role_name}
              </span>
            </td>
            <td className="px-4 py-3">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${m.status === "active"
                ? "bg-emerald-50 text-emerald-700"
                : m.status === "invited"
                  ? "bg-blue-50 text-blue-700"
                  : "bg-rose-50 text-rose-700"
                }`}>
                {m.status === "active" ? "Activo" : m.status === "invited" ? "Invitado" : "Suspendido"}
              </span>
            </td>
            <td className="px-4 py-3 text-xs text-slate-600">
              {m.branches?.length ? m.branches.join(", ") : "Alcance definido por la empresa"}
            </td>
            <td className="px-4 py-3 text-right">
              {m.status === "invited" ? (
                <div className="flex justify-end gap-2">
                  <IconAction label="Reenviar invitación" tone="neutral" disabled={!canWrite || saving} onClick={() => handleResendInvitation(m)}><RefreshCw className="h-3.5 w-3.5" /></IconAction>
                  <IconAction label="Cancelar invitación" tone="danger" disabled={!canWrite || saving} onClick={() => setCancellingInvitation(m)}><Trash2 className="h-3.5 w-3.5" /></IconAction>
                </div>
              ) : (
                <>
                  <IconAction label="Editar Permisos" tone="primary" disabled={!canWrite || saving} onClick={() => handleOpenEditor(m)}><ActionPencil aria-hidden="true" /></IconAction>
                  <IconAction label={m.is_active ? "Revisar baja" : "Reactivar"} tone="danger" disabled={!canWrite || saving} onClick={() => handleToggleActive(m)}><ActionPower aria-hidden="true" /></IconAction>
                </>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </PaginatedTable>
  </div>);
}
