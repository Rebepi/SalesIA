import { useState } from "react";
import { MemberAccessPreview, type MemberAccessImpact } from "../../components/MemberAccessPreview";
import type { useUsersAndRolesWorkspaceTab } from "../../hooks/useUsersAndRolesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { AlertTriangle, Lock, X } from "lucide-react";
import { UsersAndRolesWorkspaceTabProps } from "../../types/UsersAndRolesWorkspaceTab";

export function SeccionEditorDeRolesYPermisos({ selectedMember, setSelectedMember, escalationError, memberSecurity, securityError, targetRole, setTargetRole, setEscalationError, roles, currentUserRole, canWrite, saving, handleSaveRole }: { selectedMember: NonNullable<ReturnType<typeof useUsersAndRolesWorkspaceTab>["selectedMember"]>; setSelectedMember: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setSelectedMember"]; escalationError: ReturnType<typeof useUsersAndRolesWorkspaceTab>["escalationError"]; memberSecurity: ReturnType<typeof useUsersAndRolesWorkspaceTab>["memberSecurity"]; securityError: ReturnType<typeof useUsersAndRolesWorkspaceTab>["securityError"]; targetRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["targetRole"]; setTargetRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setTargetRole"]; setEscalationError: ReturnType<typeof useUsersAndRolesWorkspaceTab>["setEscalationError"]; roles: ReturnType<typeof useUsersAndRolesWorkspaceTab>["roles"]; saving: ReturnType<typeof useUsersAndRolesWorkspaceTab>["saving"]; handleSaveRole: ReturnType<typeof useUsersAndRolesWorkspaceTab>["handleSaveRole"] } & { currentUserRole: NonNullable<UsersAndRolesWorkspaceTabProps["currentUserRole"]>; canWrite: NonNullable<UsersAndRolesWorkspaceTabProps["canWrite"]> }) {
  const [impact, setImpact] = useState<MemberAccessImpact | null>(null);
  const [reason, setReason] = useState("");
  const [acknowledge, setAcknowledge] = useState(false);
  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true">
    <div className="app-modal-panel max-h-[90vh] overflow-y-auto w-full max-w-3xl rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="font-mono text-xs font-bold text-teal-700">{selectedMember.email}</span>
          <h3 className="font-bold text-slate-900">Editor de Roles y Permisos</h3>
        </div>
        <button onClick={() => setSelectedMember(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100">
          <X className="h-5 w-5" />
        </button>
      </div>

      {escalationError && (
        <div role="alert" className="mt-4 flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-800">
          <AlertTriangle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
          <p>{escalationError}</p>
        </div>
      )}

      <div className="mt-4 space-y-4"><section className="rounded-xl border p-3 text-xs"><h4 className="mb-2 font-bold">Seguridad del usuario</h4>{memberSecurity ? <dl className="grid grid-cols-2 gap-2"><dt>Último acceso</dt><dd>{memberSecurity.last_access ? new Date(memberSecurity.last_access).toLocaleString("es-PE", { timeZone: "America/Lima" }) : "Sin accesos registrados"}</dd><dt>MFA</dt><dd>{memberSecurity.mfa_enabled ? "Activado" : "Pendiente de configurar"}</dd><dt>Sesiones activas</dt><dd>{memberSecurity.active_sessions}</dd><dt>Invitación</dt><dd>{memberSecurity.invitation_pending ? "Pendiente de aceptar" : "Sin invitación pendiente"}</dd><dt>Credenciales</dt><dd>{memberSecurity.credentials_configured ? "Configuradas" : "Sin acceso habilitado"}</dd></dl> : <p>{securityError || "Consultando seguridad…"}</p>}</section>
        <div>
          <label htmlFor="select-new-role" className="block text-xs font-semibold text-slate-700">Asignar Rol del Sistema</label>
          <CustomSelect
            id="select-new-role"
            value={targetRole}
            onChange={(e) => {
              setTargetRole(e.target.value);
              setImpact(null);
              setAcknowledge(false);
              setEscalationError("");
            }}
            className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
          >
            {roles.map((r) => (
              <option key={r.role} value={r.role}>
                {r.title}
              </option>
            ))}
          </CustomSelect>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">Resumen de Cambios</h4>
          <div className="flex justify-between text-xs">
            <span className="text-slate-500">Rol previo:</span>
            <span className="font-semibold text-slate-700">{selectedMember.role_name}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-500">Nuevo rol seleccionado:</span>
            <span className="font-bold text-teal-800">
              {roles.find((r) => r.role === targetRole)?.title}
            </span>
          </div>
        </div>

        <MemberAccessPreview identifier={selectedMember.id} role={targetRole} onLoaded={setImpact} />
        <label className="grid gap-1 text-xs font-semibold text-slate-700">Motivo del cambio de permisos<textarea className="rounded-lg border border-slate-300 p-2 text-sm" minLength={5} maxLength={2000} required disabled={saving || !canWrite} value={reason} onChange={event => setReason(event.target.value)} /></label>
        {Boolean(impact?.responsibilities_at_risk.length) && <label className="flex gap-2 text-xs text-amber-900"><input type="checkbox" checked={acknowledge} disabled={saving || !canWrite} onChange={event => setAcknowledge(event.target.checked)} />Reconozco los pendientes que perderían permisos. Coordinaré su traspaso o resolución y el cambio no los dará por completados.</label>}
        <div className="flex items-center gap-2 rounded-xl bg-slate-100 p-3 text-xs text-slate-600">
          <Lock className="h-4 w-4 text-slate-500 shrink-0" />
          <span>Tu rol actual es <strong>{currentUserRole}</strong>. El servidor impide delegar permisos que tu cuenta no posee.</span>
        </div>
      </div>

      <div className="mt-6 flex justify-end gap-2">
        <button
          onClick={() => setSelectedMember(null)}
          className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
        >
          Cancelar
        </button>
        <button
          disabled={!canWrite || saving || !targetRole || targetRole === selectedMember.role || !impact?.can_assign_target || reason.trim().length < 5 || Boolean(impact?.responsibilities_at_risk.length && !acknowledge)}
          onClick={() => { if (impact) void handleSaveRole({ reason, access_hash: impact.access_hash, acknowledge_responsibilities: acknowledge }); }}
          className="rounded-xl bg-teal-700 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Confirmar Cambios
        </button>
      </div>
    </div>
  </div>);
}
