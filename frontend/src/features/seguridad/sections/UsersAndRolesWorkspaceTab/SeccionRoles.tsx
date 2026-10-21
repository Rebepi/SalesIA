import { IconAction } from "../../../../ui/components/primitives/IconAction";
import { Trash2 as ActionTrash2 } from "lucide-react";
import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { ChevronLeft, ChevronRight, Copy, ShieldCheck } from "lucide-react";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";

export function SeccionRoles({ visibleRoles, roleDisplay, canWrite, saving, setManagedRole, openRoleCreator, roleRangeStart, roleRangeEnd, filteredRoles, rolePageSize, setRolePageSize, setRolePage, rolePage, roleTotalPages }: { visibleRoles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["visibleRoles"]; roleDisplay: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleDisplay"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"]; setManagedRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setManagedRole"]; openRoleCreator: ReturnType<typeof useUsersAndRolesWorkspaceTab>["openRoleCreator"]; roleRangeStart: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleRangeStart"]; roleRangeEnd: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleRangeEnd"]; filteredRoles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["filteredRoles"]; rolePageSize: ReturnType<typeof useUsersAndRolesWorkspaceTab>["rolePageSize"]; setRolePageSize: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRolePageSize"]; setRolePage: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRolePage"]; rolePage: ReturnType<typeof useUsersAndRolesWorkspaceTab>["rolePage"]; roleTotalPages: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleTotalPages"] } & { canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  return (<div className="flex flex-col flex-1 min-h-0 gap-3">
    <div className="flex-1 min-h-0 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      {visibleRoles.length === 0 ? (
        <div className="flex min-h-52 flex-col items-center justify-center text-center">
          <ShieldCheck className="h-9 w-9 text-slate-300" />
          <p className="mt-3 font-semibold text-slate-700">No se encontraron roles</p>
          <p className="mt-1 text-sm text-slate-500">Prueba con otro nombre, código o descripción.</p>
        </div>
      ) : roleDisplay === "cards" ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visibleRoles.map((role) => (
            <article key={role.role} className="flex min-h-[230px] flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${role.is_custom ? "bg-violet-50 text-violet-700" : "bg-slate-100 text-slate-600"}`}>
                  {role.is_custom ? "Personalizado" : "Rol del sistema"}
                </span>
              </div>
              <h3 className="mt-4 text-base font-bold text-slate-900">{role.title}</h3>
              <p className="mt-1 font-mono text-[11px] text-slate-400">{role.role}</p>
              <p className="mt-3 flex-1 text-sm leading-6 text-slate-600">{role.description || "Rol empresarial personalizado."}</p>
              <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
                <span className="text-xs font-semibold text-slate-500">{role.permissions.length} permisos</span>{role.is_custom && canWrite && <IconAction label="Editar / eliminar" tone="primary" disabled={saving} onClick={() => setManagedRole(role)}><ActionTrash2 aria-hidden="true" /></IconAction>}
                <IconAction label="Usar como plantilla" tone="neutral" disabled={!canWrite || saving} onClick={() => openRoleCreator(role)}><Copy className="h-3.5 w-3.5" /></IconAction>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-100 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Descripción</th>
                <th className="px-4 py-3 text-center">Permisos</th>
                <th className="px-4 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visibleRoles.map((role) => (
                <tr key={role.role} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-slate-900">{role.title}</p>
                    <p className="mt-0.5 font-mono text-[11px] text-slate-400">{role.role}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${role.is_custom ? "bg-violet-50 text-violet-700" : "bg-slate-100 text-slate-600"}`}>
                      {role.is_custom ? "Personalizado" : "Del sistema"}
                    </span>
                  </td>
                  <td className="max-w-md px-4 py-3 text-slate-600">{role.description || "Rol empresarial personalizado."}</td>
                  <td className="px-4 py-3 text-center font-semibold text-slate-600">{role.permissions.length}</td>
                  <td className="px-4 py-3 text-right">
                    <IconAction label="Usar como plantilla" tone="neutral" disabled={!canWrite || saving} onClick={() => openRoleCreator(role)}><Copy className="h-3.5 w-3.5" /></IconAction>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>

    <div className="shrink-0 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white px-5 py-3.5">
      <p className="text-sm text-slate-500">{roleRangeStart}-{roleRangeEnd} de {filteredRoles.length} roles</p>
      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="role-page-size" className="text-sm text-slate-500">Roles por página</label>
        <select
          id="role-page-size"
          value={rolePageSize}
          onChange={(event) => setRolePageSize(Number(event.target.value))}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-teal-500"
        >
          <option value={6}>6</option>
          <option value={9}>9</option>
          <option value={12}>12</option>
          <option value={24}>24</option>
        </select>
        <IconAction label="Página anterior" tone="neutral" onClick={() => setRolePage((current) => Math.max(1, current - 1))} disabled={rolePage === 1} aria-label="Página anterior"><ChevronLeft className="h-4 w-4" /></IconAction>
        <span className="min-w-24 text-center text-sm font-semibold text-slate-700">Página {rolePage} de {roleTotalPages}</span>
        <IconAction label="Página siguiente" tone="neutral" onClick={() => setRolePage((current) => Math.min(roleTotalPages, current + 1))} disabled={rolePage === roleTotalPages} aria-label="Página siguiente"><ChevronRight className="h-4 w-4" /></IconAction>
      </div>
    </div>

  </div>);
}
