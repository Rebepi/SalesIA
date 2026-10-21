import { apiClient } from "../../../api/client";
import { MemberItem } from "../types/UsersAndRolesWorkspaceTab";
import { RoleItem } from "../types/UsersAndRolesWorkspaceTab";

export function solicitarDatos() {
  return apiClient.request<{ roles: RoleItem[]; all_permissions: string[] }>("/api/v1/roles");
}

export function solicitarHandleOpenEditor({ member }: { member: MemberItem }) {
  return apiClient.request<{ mfa_enabled: boolean; last_access?: string; active_sessions: number; invitation_pending: boolean; credentials_configured: boolean }>(`/api/v1/users/${member.id}/security`);
}

export function solicitarHandleSaveRole({ selectedMember, targetRole, review }: { selectedMember: MemberItem; targetRole: string; review: { reason: string; access_hash: string; acknowledge_responsibilities: boolean } }) {
  return apiClient.request(`/api/v1/memberships/${selectedMember.id}`, { method: "PATCH", body: JSON.stringify({ role: targetRole, ...review }) });
}

export function solicitarHandleInvite({ inviteEmail, inviteRole }: { inviteEmail: string; inviteRole: string }) {
  return apiClient.request<{ invitation_id: string; user_id: string; email: string; role: string }>("/api/v1/memberships/invitations", { method: "POST", body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }) });
}

export function solicitarHandleToggleActive({ member, isActive }: { member: MemberItem; isActive: boolean }) {
  return apiClient.request(`/api/v1/memberships/${member.id}`, { method: "PATCH", body: JSON.stringify({ is_active: isActive }) });
}

export function solicitarHandleResendInvitation({ member }: { member: MemberItem }) {
  return apiClient.request(`/api/v1/memberships/invitations/${member.id}/resend`, { method: "POST" });
}

export function solicitarHandleCancelInvitation({ cancellingInvitation }: { cancellingInvitation: MemberItem }) {
  return apiClient.request(`/api/v1/memberships/invitations/${cancellingInvitation.id}`, { method: "DELETE" });
}

export function solicitarHandleCreateRole({ roleKey, roleTitle, roleDescription, selectedPermissions }: { roleKey: string; roleTitle: string; roleDescription: string; selectedPermissions: string[] }) {
  return apiClient.request<RoleItem>("/api/v1/roles", {
    method: "POST",
    body: JSON.stringify({
      role_key: roleKey,
      title: roleTitle.trim(),
      description: roleDescription.trim(),
      permissions: selectedPermissions
    })
  });
}
