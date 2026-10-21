import * as transporte from "../api/UserProfilePreferencesWorkspaceTab";
import { useEffect, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { UserSessionItem } from "../types/UserProfilePreferencesWorkspaceTab";
import { UserProfilePreferencesWorkspaceTabProps } from "../types/UserProfilePreferencesWorkspaceTab";

export function useUserProfilePreferencesWorkspaceTab(_props: UserProfilePreferencesWorkspaceTabProps) {
  const [fullName, setFullName] = useState<string>("");

  const [email, setEmail] = useState<string>("");

  const [phone, setPhone] = useState<string>("");

  const [role, setRole] = useState<string>("");

  const [mfaActive, setMfaActive] = useState<boolean>(false);

  const [sessions, setSessions] = useState<UserSessionItem[]>([]);

  const [loading, setLoading] = useState(true);

  const [saving, setSaving] = useState(false);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [setupOpen, setSetupOpen] = useState(false);

  const [setupSecret, setSetupSecret] = useState("");

  const [setupBusy, setSetupBusy] = useState(false);

  const [sudoModalOpen, setSudoModalOpen] = useState(false);

  const [password, setPassword] = useState("");

  const [mfaCode, setMfaCode] = useState("");

  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);

  const toast = useToast();

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      transporte.solicitarDatos(),
      transporte.solicitarDatos2()
    ])
      .then(([profile, sessionItems]) => {
        if (!active) return;
        setFullName(profile.full_name);
        setEmail(profile.email);
        setPhone(profile.phone);
        setRole(profile.role);
        setMfaActive(profile.mfa_enabled);
        if (sessionItems) {
          setSessions(sessionItems.map((session) => ({ session_id: session.session_id, device_name: session.user_agent || "Dispositivo no identificado", ip_address: session.ip_address || "No disponible", last_active: session.is_current ? "Activa ahora" : `Iniciada ${new Date(session.created_at).toLocaleString("es-PE")}`, is_current: session.is_current })));
        }
        setLoadError(null);
      })
      .catch((failure: unknown) => {
        if (active) setLoadError(String((failure as { detail?: string }).detail || failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const handleSetupMfa = async (event: React.FormEvent) => {
    event.preventDefault();
    if (setupBusy) return;
    setSetupBusy(true);
    try {
      if (setupSecret) {
        await transporte.solicitarHandleSetupMfa({ mfaCode });
        setMfaActive(true);
        setSessions(previous => previous.filter(session => session.is_current));
        setSetupOpen(false);
        setSetupSecret("");
        setMfaCode("");
        toast.success("Autenticación activada", "Tu cuenta está protegida con un segundo factor.");
      } else {
        const result = await transporte.solicitarHandleSetupMfa2({ password });
        setSetupSecret(result.totp_secret);
        setRecoveryCodes(result.recovery_codes);
        setPassword("");
      }
    } catch (failure: unknown) {
      toast.error("No se pudo configurar MFA", String((failure as { detail?: string }).detail || failure));
    } finally { setSetupBusy(false); }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await transporte.solicitarHandleRevokeSession({ sessionId });
      setSessions((prev) => prev.filter((session) => session.session_id !== sessionId));
      toast.success("Sesión revocada", "El token de la sesión seleccionada fue invalidado.");
    } catch (failure: unknown) {
      toast.error("No se pudo revocar la sesión", String((failure as { detail?: string }).detail || failure));
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading || loadError || saving) return;
    setSaving(true);
    try {
      await transporte.solicitarHandleSavePreferences({ fullName, phone });
      toast.success("Datos guardados", "Tus datos personales fueron actualizados.");
    } catch (failure: unknown) {
      toast.error("No se pudieron guardar las preferencias", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerateCodes = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await transporte.solicitarHandleRegenerateCodes({ password, mfaCode });
      const response = await transporte.solicitarHandleRegenerateCodes2();
      setRecoveryCodes(response.recovery_codes);
      setPassword("");
      setMfaCode("");
      setSudoModalOpen(false);
      toast.success("Códigos regenerados", "Los códigos anteriores fueron invalidados.");
    } catch (failure: unknown) {
      toast.error("No se pudieron regenerar los códigos", String((failure as { detail?: string }).detail || failure));
    }
  };
  return { fullName, setFullName, email, phone, setPhone, role, mfaActive, sessions, loading, saving, loadError, setupOpen, setSetupOpen, setupSecret, setupBusy, sudoModalOpen, setSudoModalOpen, password, setPassword, mfaCode, setMfaCode, recoveryCodes, setRecoveryCodes, handleSetupMfa, handleRevokeSession, handleSavePreferences, handleRegenerateCodes };
}
