import { apiClient } from "../../../api/client";

export function solicitarDatos() {
  return apiClient.request<{ full_name: string; email: string; phone: string; role: string; mfa_enabled: boolean }>("/api/v1/auth/profile");
}

export function solicitarDatos2() {
  return apiClient.request<Array<{ session_id: string; user_agent: string; ip_address: string; created_at: string; is_current: boolean }>>("/api/v1/auth/sessions");
}

export function solicitarHandleSetupMfa({ mfaCode }: { mfaCode: string }) {
  return apiClient.request("/api/v1/auth/mfa/verify", { method: "POST", body: JSON.stringify({ code: mfaCode }) });
}

export function solicitarHandleSetupMfa2({ password }: { password: string }) {
  return apiClient.request<{ totp_secret: string; recovery_codes: string[] }>("/api/v1/auth/mfa/setup", { method: "POST", body: JSON.stringify({ password }) });
}

export function solicitarHandleRevokeSession({ sessionId }: { sessionId: string }) {
  return apiClient.request(`/api/v1/auth/sessions/${sessionId}`, { method: "DELETE" });
}

export function solicitarHandleSavePreferences({ fullName, phone }: { fullName: string; phone: string }) {
  return apiClient.request("/api/v1/auth/profile", { method: "PATCH", body: JSON.stringify({ full_name: fullName, phone }) });
}

export function solicitarHandleRegenerateCodes({ password, mfaCode }: { password: string; mfaCode: string }) {
  return apiClient.request("/api/v1/auth/sudo/verify", { method: "POST", body: JSON.stringify({ password, mfa_code: mfaCode || null }) });
}

export function solicitarHandleRegenerateCodes2() {
  return apiClient.request<{ recovery_codes: string[] }>("/api/v1/auth/mfa/recovery-codes/regenerate", { method: "POST" });
}
