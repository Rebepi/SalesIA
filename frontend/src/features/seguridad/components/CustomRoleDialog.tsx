import { ModalSurface } from "../../../ui/components/ModalSurface";
import { FormEvent, useEffect, useState } from "react";
import { X } from "lucide-react";
import { apiClient } from "../../../api/client";
import { CustomSelect } from "../../../ui/components/CustomSelect";
import { useConfirm } from "../../../ui/components/ConfirmDialog";

interface Role { role: string; title: string; description?: string; permissions: string[] }
interface Impact { role_hash: string; title: string; description: string; permissions: string[]; affected_users: number; users: Array<{ name: string; email: string; is_active: boolean }> }

export function CustomRoleDialog({ role, roles, availablePermissions, onClose, onSaved }: { role: Role; roles: Role[]; availablePermissions: string[]; onClose: () => void; onSaved: () => void }) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [title, setTitle] = useState(role.title);
  const [description, setDescription] = useState(role.description || "");
  const [permissions, setPermissions] = useState(role.permissions);
  const [replacement, setReplacement] = useState("");
  const [impact, setImpact] = useState<Impact | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [reason, setReason] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => { const controller = new AbortController(); setImpact(null); void apiClient.request<Impact>(`/api/v1/roles/${encodeURIComponent(role.role)}/impact`, { signal: controller.signal }).then(row => { if (!controller.signal.aborted) { setImpact(row); setTitle(row.title); setDescription(row.description); setPermissions(row.permissions); } }).catch(failure => { if (!controller.signal.aborted) setError(String(failure?.detail || "No se pudo calcular el impacto.")); }); return () => controller.abort(); }, [role.role, revision]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!impact || busy) return;
    if (!await confirm({ title: deleting ? "¿Eliminar rol?" : "¿Actualizar rol?", text: `${deleting ? "Se eliminará el rol y se asignará el reemplazo elegido" : "Se cambiarán el nombre y los permisos del rol"}. Se afectará a ${impact.affected_users} usuarios y se cerrarán sus sesiones.`, danger: deleting, confirmLabel: deleting ? "Eliminar" : "Actualizar" })) return;
    setBusy(true);
    setError("");
    try {
      await apiClient.request(`/api/v1/roles/${encodeURIComponent(role.role)}${deleting ? `?affected_users=${impact.affected_users}${replacement ? `&replacement_role=${encodeURIComponent(replacement)}` : ""}` : ""}`, { method: deleting ? "DELETE" : "PATCH", body: deleting ? undefined : JSON.stringify({ title, description, permissions, affected_users: impact.affected_users, expected_role_hash: impact.role_hash, reason }) });
      onSaved();
    } catch (failure: unknown) { setError(String((failure as { detail?: string }).detail || "No se pudo actualizar el rol. Revisa el impacto y vuelve a intentar.")); }
    finally { setBusy(false); }
  }
  return (
    <>
      <ModalSurface labelledBy="custom-role-manage-title" onClose={onClose} blocked={busy}><form onSubmit={submit} className="app-modal-panel max-h-[90vh] w-full max-w-3xl space-y-4 overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><header className="flex items-center justify-between"><h3 id="custom-role-manage-title" className="font-bold">Administrar rol {role.title}</h3><button type="button" onClick={onClose} disabled={busy} aria-label="Cerrar administración de rol"><X className="h-5 w-5" /></button></header><section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900"><strong>{impact ? `${impact.affected_users} usuarios afectados` : "Calculando usuarios afectados…"}</strong><div className="mt-2 max-h-32 space-y-1 overflow-y-auto">{impact?.users.map(user => <p key={user.email}>{user.name} · {user.email} · {user.is_active ? "Activo" : "Inactivo"}</p>)}</div><p className="mt-2">Las sesiones afectadas se cerrarán. Los cambios de permisos pueden revertirse editando el rol nuevamente.</p></section><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={deleting} onChange={event => setDeleting(event.target.checked)} />Eliminar este rol personalizado</label>{deleting ? <label className="block text-xs font-semibold">Rol de reemplazo<CustomSelect value={replacement} onChange={event => setReplacement(event.target.value)} required={Boolean(impact?.affected_users)} className="mt-1 w-full rounded-xl border p-2.5"><option value="">Seleccionar reemplazo</option>{roles.filter(item => item.role !== role.role).map(item => <option key={item.role} value={item.role}>{item.title}</option>)}</CustomSelect></label> : <><label className="block text-xs font-semibold">Nombre visible<input value={title} onChange={event => setTitle(event.target.value)} required maxLength={128} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label><label className="block text-xs font-semibold">Descripción<textarea value={description} onChange={event => setDescription(event.target.value)} maxLength={2000} className="mt-1 w-full rounded-xl border p-2.5 dark:bg-slate-950" /></label><fieldset className="rounded-xl border p-3"><legend className="px-1 text-xs font-bold">Permisos</legend><div className="grid max-h-64 gap-2 overflow-y-auto sm:grid-cols-2">{availablePermissions.map(permission => <label key={permission} className="flex gap-2 text-xs"><input type="checkbox" checked={permissions.includes(permission)} onChange={event => setPermissions(previous => event.target.checked ? [...previous, permission] : previous.filter(item => item !== permission))} />{permission}</label>)}</div></fieldset></>}{!deleting && <><label className="block text-xs font-semibold">Motivo del cambio<textarea value={reason} onChange={event => setReason(event.target.value)} required minLength={5} maxLength={2000} disabled={busy} className="mt-1 w-full rounded-xl border p-2.5" /></label><div className="rounded border p-3 text-xs"><p>Permisos que se añaden: {permissions.filter(value => !impact?.permissions.includes(value)).join(", ") || "Ninguno"}.</p><p>Permisos que se retiran: {impact?.permissions.filter(value => !permissions.includes(value)).join(", ") || "Ninguno"}.</p></div></>}<button type="button" disabled={busy} className="rounded border px-3 py-2 text-xs" onClick={() => setRevision(value => value + 1)}>Actualizar impacto y configuración</button>{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-xs text-red-800">{error}</p>}<footer className="flex justify-end gap-2"><button type="button" onClick={onClose} disabled={busy} className="rounded-xl border px-4 py-2 text-xs">Cancelar</button><button type="submit" disabled={busy || !impact} className={`rounded-xl px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 ${deleting ? "bg-red-700" : "bg-teal-700"}`}>{busy ? "Guardando…" : deleting ? "Eliminar y reasignar" : "Guardar cambios"}</button></footer></form></ModalSurface>
      {ConfirmDialogNode}
    </>
  );
}
