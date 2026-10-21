import { SeccionDatosPersonalesYDeContacto } from "../sections/UserProfilePreferencesWorkspaceTab/SeccionDatosPersonalesYDeContacto";
export type { UserSessionItem } from "../types/UserProfilePreferencesWorkspaceTab";
export type { UserProfilePreferencesWorkspaceTabProps } from "../types/UserProfilePreferencesWorkspaceTab";
import { useUserProfilePreferencesWorkspaceTab } from "../hooks/useUserProfilePreferencesWorkspaceTab";
import { NavbarSectionHeader } from "../../../ui/components/NavbarSectionHeader";
import { UserProfilePreferencesWorkspaceTabProps } from "../types/UserProfilePreferencesWorkspaceTab";

export function UserProfilePreferencesWorkspaceTab({ canWrite: _canWrite = true }: UserProfilePreferencesWorkspaceTabProps) {
  const { fullName, setFullName, email, phone, setPhone, role, mfaActive, sessions, loading, saving, loadError, setupOpen, setSetupOpen, setupSecret, setupBusy, sudoModalOpen, setSudoModalOpen, password, setPassword, mfaCode, setMfaCode, recoveryCodes, setRecoveryCodes, handleSetupMfa, handleRevokeSession, handleSavePreferences, handleRegenerateCodes } = useUserProfilePreferencesWorkspaceTab({ canWrite: _canWrite });
  return (
    <div id="scr-050-profile-preferences" data-testid="scr-050-profile-preferences" className="space-y-6">
      <NavbarSectionHeader view="profile_preferences" className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="workspace-eyebrow">CUENTA</span>
            <h1 className="text-xl font-bold text-slate-900">Mi cuenta</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Datos personales, sesiones activas y autenticación de dos factores (MFA).
          </p>
        </div>
      </NavbarSectionHeader>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Cargando perfil y sesiones activas...</div>}
      {loadError && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{loadError}</div>}

      <SeccionDatosPersonalesYDeContacto handleSavePreferences={handleSavePreferences} saving={saving} fullName={fullName} setFullName={setFullName} email={email} phone={phone} setPhone={setPhone} role={role} mfaActive={mfaActive} setPassword={setPassword} setMfaCode={setMfaCode} setSudoModalOpen={setSudoModalOpen} setSetupOpen={setSetupOpen} recoveryCodes={recoveryCodes} setRecoveryCodes={setRecoveryCodes} sessions={sessions} handleRevokeSession={handleRevokeSession} loading={loading} loadError={loadError} />

      {setupOpen && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true" aria-labelledby="setup-mfa-title">
        <form onSubmit={handleSetupMfa} className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4">
          <h2 id="setup-mfa-title" className="font-bold text-slate-900">Configurar autenticación de dos factores</h2>
          {setupSecret ? <>
            <p className="text-sm text-slate-500">Añade esta clave a tu aplicación de autenticación y escribe el código generado.</p>
            <code className="block break-all rounded-xl bg-slate-100 p-3 text-slate-900">{setupSecret}</code>
            <label className="block text-sm text-slate-700">Código de verificación<input required autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" value={mfaCode} onChange={event => setMfaCode(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 p-3" /></label>
          </> : <label className="block text-sm text-slate-700">Contraseña actual<input required type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 p-3" /></label>}
          <div className="flex justify-end gap-2">
            <button type="button" disabled={setupBusy} onClick={() => { setSetupOpen(false); setPassword(""); setMfaCode(""); }} className="rounded-xl border border-slate-300 px-4 py-2 text-slate-700">Cerrar</button>
            <button disabled={setupBusy} className="rounded-xl bg-teal-700 px-4 py-2 text-white">{setupBusy ? "Procesando…" : setupSecret ? "Activar MFA" : "Continuar"}</button>
          </div>
        </form>
      </div>}
      {sudoModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" role="dialog" aria-modal="true">
          <form onSubmit={handleRegenerateCodes} className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900">Reautenticación requerida</h3>
            <p className="mt-1 text-xs text-slate-500">Confirma tu contraseña y el código MFA actual. Al continuar, todos los códigos de respaldo anteriores quedarán invalidados.</p>
            <label className="mt-4 block text-xs font-semibold text-slate-700" htmlFor="sudo-password">Contraseña</label>
            <input id="sudo-password" type="password" required value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <label className="mt-4 block text-xs font-semibold text-slate-700" htmlFor="sudo-mfa">Código MFA</label>
            <input id="sudo-mfa" inputMode="numeric" required={mfaActive} value={mfaCode} onChange={(event) => setMfaCode(event.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm" />
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" onClick={() => setSudoModalOpen(false)} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">Cancelar</button>
              <button type="submit" className="rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white">Regenerar códigos</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
