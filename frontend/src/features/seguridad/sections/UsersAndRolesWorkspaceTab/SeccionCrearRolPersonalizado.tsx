import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { Check, Search, ShieldCheck, X } from "lucide-react";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";
import { permissionLabels } from "../../support/UsersAndRolesWorkspaceTab";
import { permissionGroupLabels } from "../../support/UsersAndRolesWorkspaceTab";

export function SeccionCrearRolPersonalizado({ handleCreateRole, setRoleModalOpen, roleTitle, roleKeyFromTitle, setRoleTitle, roleKey, setRoleKey, roleDescription, setRoleDescription, selectedPermissions, allPermissions, permissionSearch, setPermissionSearch, permissionGroups, setSelectedPermissions, togglePermission, canWrite, saving }: { handleCreateRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleCreateRole"]; setRoleModalOpen: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRoleModalOpen"]; roleTitle: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleTitle"]; roleKeyFromTitle: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleKeyFromTitle"]; setRoleTitle: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRoleTitle"]; roleKey: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleKey"]; setRoleKey: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRoleKey"]; roleDescription: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roleDescription"]; setRoleDescription: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setRoleDescription"]; selectedPermissions: ReturnType<typeof useUsersAndRolesWorkspaceTab>["selectedPermissions"]; allPermissions: ReturnType<typeof useUsersAndRolesWorkspaceTab>["allPermissions"]; permissionSearch: ReturnType<typeof useUsersAndRolesWorkspaceTab>["permissionSearch"]; setPermissionSearch: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setPermissionSearch"]; permissionGroups: ReturnType<typeof useUsersAndRolesWorkspaceTab>["permissionGroups"]; setSelectedPermissions: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setSelectedPermissions"]; togglePermission: ReturnType<typeof useUsersAndRolesWorkspaceTab>["togglePermission"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"] } & { canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" role="dialog" aria-modal="true" aria-labelledby="create-role-title">
    <form onSubmit={handleCreateRole} className="app-modal-panel flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
      <div className="flex items-start justify-between border-b border-slate-100 px-6 py-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 id="create-role-title" className="font-bold text-slate-900">Crear rol personalizado</h3>
              <p className="text-xs text-slate-500">Define el alcance exacto que tendrá este perfil dentro de la empresa.</p>
            </div>
          </div>
        </div>
        <button type="button" onClick={() => setRoleModalOpen(false)} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100" aria-label="Cerrar">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="overflow-y-auto px-6 py-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="custom-role-title" className="block text-xs font-semibold text-slate-700">Nombre visible</label>
            <input
              id="custom-role-title"
              required
              value={roleTitle}
              onChange={(event) => {
                const previousGeneratedKey = roleKeyFromTitle(roleTitle);
                const nextTitle = event.target.value;
                setRoleTitle(nextTitle);
                if (!roleKey || roleKey === previousGeneratedKey) setRoleKey(roleKeyFromTitle(nextTitle));
              }}
              placeholder="Ej. Supervisor de Ventas"
              className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
            />
          </div>
          <div>
            <label htmlFor="custom-role-key" className="block text-xs font-semibold text-slate-700">Código interno</label>
            <input
              id="custom-role-key"
              required
              minLength={3}
              maxLength={64}
              pattern="[a-z][a-z0-9_]{2,63}"
              value={roleKey}
              onChange={(event) => setRoleKey(roleKeyFromTitle(event.target.value))}
              placeholder="supervisor_ventas"
              className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2.5 font-mono text-sm"
            />
            <p className="mt-1 text-[11px] text-slate-400">Se usa internamente y no puede repetirse.</p>
          </div>
        </div>

        <div className="mt-4">
          <label htmlFor="custom-role-description" className="block text-xs font-semibold text-slate-700">Descripción</label>
          <textarea
            id="custom-role-description"
            rows={2}
            value={roleDescription}
            onChange={(event) => setRoleDescription(event.target.value)}
            placeholder="Describe las responsabilidades principales de este rol."
            className="mt-1.5 w-full resize-none rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          />
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Permisos del rol</h4>
            <p className="text-xs text-slate-500">Seleccionados: {selectedPermissions.length} de {allPermissions.length}</p>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              value={permissionSearch}
              onChange={(event) => setPermissionSearch(event.target.value)}
              placeholder="Buscar permiso..."
              className="w-full rounded-xl border border-slate-300 py-2 pl-9 pr-3 text-sm"
            />
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {Object.entries(permissionGroups).map(([group, permissions]) => (
            <section key={group} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h5 className="text-xs font-bold uppercase tracking-wide text-slate-600">{permissionGroupLabels[group] || group}</h5>
                <button
                  type="button"
                  onClick={() => setSelectedPermissions((current) => Array.from(new Set([...current, ...permissions])))}
                  className="text-[11px] font-semibold text-teal-700 hover:text-teal-800"
                >
                  Seleccionar grupo
                </button>
              </div>
              <div className="space-y-2">
                {permissions.map((permission) => {
                  const checked = selectedPermissions.includes(permission);
                  return (
                    <button
                      key={permission}
                      type="button"
                      role="checkbox"
                      aria-checked={checked}
                      onClick={() => togglePermission(permission)}
                      className={`flex w-full items-start gap-2.5 rounded-lg border px-3 py-2.5 text-left transition ${checked ? "border-teal-300 bg-teal-50" : "border-transparent bg-white hover:border-slate-200"}`}
                    >
                      <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${checked ? "border-teal-600 bg-teal-600 text-white" : "border-slate-300 bg-white"}`}>
                        {checked && <Check className="h-3 w-3" />}
                      </span>
                      <span>
                        <span className="block text-xs font-semibold text-slate-700">{permissionLabels[permission] || permission}</span>
                        <span className="mt-0.5 block font-mono text-[10px] text-slate-400">{permission}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-6 py-4">
        <p className="hidden text-xs text-slate-500 sm:block">Los permisos superiores a los tuyos serán rechazados por el servidor.</p>
        <div className="ml-auto flex gap-2">
          <button type="button" onClick={() => setRoleModalOpen(false)} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={!canWrite || saving || roleKey.length < 3 || !roleTitle.trim()}
            className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Creando..." : "Crear rol"}
          </button>
        </div>
      </div>
    </form>
  </div>);
}
