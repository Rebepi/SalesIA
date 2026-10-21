import type { useUserProfilePreferencesWorkspaceTab } from "../../hooks/useUserProfilePreferencesWorkspaceTab";
import { Laptop, LogOut, ShieldCheck, Smartphone } from "lucide-react";
import { describeDevice } from "../../support/UserProfilePreferencesWorkspaceTab";

export function SeccionDatosPersonalesYDeContacto({ handleSavePreferences, saving, fullName, setFullName, email, phone, setPhone, role, mfaActive, setPassword, setMfaCode, setSudoModalOpen, setSetupOpen, recoveryCodes, setRecoveryCodes, sessions, handleRevokeSession, loading, loadError }: { handleSavePreferences: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["handleSavePreferences"]; saving: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["saving"]; fullName: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["fullName"]; setFullName: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setFullName"]; email: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["email"]; phone: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["phone"]; setPhone: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setPhone"]; role: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["role"]; mfaActive: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["mfaActive"]; setPassword: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setPassword"]; setMfaCode: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setMfaCode"]; setSudoModalOpen: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setSudoModalOpen"]; setSetupOpen: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setSetupOpen"]; recoveryCodes: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["recoveryCodes"]; setRecoveryCodes: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["setRecoveryCodes"]; sessions: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["sessions"]; handleRevokeSession: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["handleRevokeSession"]; loading: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["loading"]; loadError: ReturnType<typeof useUserProfilePreferencesWorkspaceTab>["loadError"] }) {
  return (<form onSubmit={handleSavePreferences} className="space-y-6" aria-busy={saving}>
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <h2 className="text-base font-bold text-slate-900">Datos Personales y de Contacto</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="pref-name-input" className="block text-xs font-semibold text-slate-700">Nombre Completo</label>
          <input
            id="pref-name-input"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800"
          />
        </div>

        <div>
          <label htmlFor="pref-email-input" className="block text-xs font-semibold text-slate-700">Correo Electrónico</label>
          <input
            id="pref-email-input"
            type="email"
            value={email}
            readOnly
            className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-600"
          />
        </div>

        <div>
          <label htmlFor="pref-phone-input" className="block text-xs font-semibold text-slate-700">Teléfono Móvil</label>
          <input
            id="pref-phone-input"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800"
          />
        </div>

        <div>
          <span className="block text-xs font-semibold text-slate-700">Rol Asignado en la Empresa</span>
          <div className="mt-1.5 flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-2 text-sm text-slate-700 font-semibold">
            <ShieldCheck className="h-4 w-4 text-teal-700" />
            <span>{role || "Rol no disponible"}</span>
          </div>
        </div>
      </div>
    </div>

    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <h2 className="text-base font-bold text-slate-900">Seguridad y Autenticación de Dos Factores (MFA)</h2>
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-sm text-slate-900">Segundo Factor TOTP (Google Authenticator / Authy)</h3>
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-700 border border-emerald-200">
              {mfaActive ? "Activado y Requerido" : "Pendiente"}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            La política corporativa exige autenticación de dos factores en todas las cuentas con roles administrativos.
          </p>
        </div>
        <button
          type="button"
          onClick={() => { setPassword(""); setMfaCode(""); mfaActive ? setSudoModalOpen(true) : setSetupOpen(true); }}
          className="rounded-xl border border-slate-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          {mfaActive ? "Regenerar Códigos de Respaldo" : "Configurar MFA"}
        </button>
      </div>
      {recoveryCodes.length > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4">
          <h3 className="text-sm font-bold text-amber-900">Guarda estos códigos ahora</h3>
          <p className="mt-1 text-xs text-amber-800">Cada código funciona una sola vez y no volverá a mostrarse.</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {recoveryCodes.map((code) => <code key={code} className="rounded-lg bg-white px-3 py-2 text-xs text-slate-900 border border-amber-200">{code}</code>)}
          </div>
          <button type="button" onClick={() => setRecoveryCodes([])} className="mt-3 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900">Ya los guardé</button>
        </div>
      )}
    </div>


    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <h2 className="text-base font-bold text-slate-900">Sesiones Activas</h2>
      <div className="max-h-[440px] overflow-y-auto space-y-3 pr-1">
        {sessions.map((sess) => (
          <div key={sess.session_id} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex items-center gap-3">
              {sess.device_name.includes("Móvil") ? (
                <Smartphone className="h-5 w-5 text-slate-400" />
              ) : (
                <Laptop className="h-5 w-5 text-slate-400" />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <h3 title={sess.device_name} className="break-words font-semibold text-xs text-slate-900">{describeDevice(sess.device_name)}</h3>
                  {sess.is_current && (
                    <span className="rounded-full bg-teal-50 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                      Sesión Actual
                    </span>
                  )}
                </div>
                <p className="text-[11px] font-mono text-slate-400">
                  IP: {sess.ip_address} · {sess.last_active}
                </p>
              </div>
            </div>

            {!sess.is_current && (
              <button
                type="button"
                onClick={() => handleRevokeSession(sess.session_id)}
                className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 hover:text-rose-900"
              >
                <LogOut className="h-3.5 w-3.5" />
                Revocar
              </button>
            )}
          </div>
        ))}
      </div>
    </div>

    <div className="flex justify-end pt-2">
      <button
        type="submit"
        disabled={loading || Boolean(loadError) || saving}
        className="rounded-xl bg-teal-700 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-800"
      >
        Guardar datos personales
      </button>
    </div>
  </form>);
}
