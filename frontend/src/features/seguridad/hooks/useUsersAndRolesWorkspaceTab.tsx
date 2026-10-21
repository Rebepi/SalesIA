import * as transporte from "../api/UsersAndRolesWorkspaceTab";
import { requestAllPages } from "../../../api/pagination";
import { useEffect, useMemo, useState } from "react";
import { useToast } from "../../../ui/toast/ToastContext";

import { useConfirm } from "../../../ui/components/ConfirmDialog";
import { MemberItem } from "../types/UsersAndRolesWorkspaceTab";
import { RoleItem } from "../types/UsersAndRolesWorkspaceTab";
import { UsersAndRolesWorkspaceTabProps } from "../types/UsersAndRolesWorkspaceTab";
import { permissionLabels } from "../support/UsersAndRolesWorkspaceTab";

export function useUsersAndRolesWorkspaceTab({ canWrite = true, currentUserRole = "company_admin" }: UsersAndRolesWorkspaceTabProps) {
  const { confirm, ConfirmDialogNode } = useConfirm();

  const [members, setMembers] = useState<MemberItem[]>([]);

  const [roles, setRoles] = useState<RoleItem[]>([]);

  const [allPermissions, setAllPermissions] = useState<string[]>([]);

  const [workspaceView, setWorkspaceView] = useState<"members" | "roles">("members");

  const [loading, setLoading] = useState(true);

  const [loadError, setLoadError] = useState<string | null>(null);

  const [selectedMember, setSelectedMember] = useState<MemberItem | null>(null);

  const [targetRole, setTargetRole] = useState<string>("");

  const [escalationError, setEscalationError] = useState<string>("");

  const [inviteModalOpen, setInviteModalOpen] = useState(false);

  const [inviteEmail, setInviteEmail] = useState("");

  const [inviteRole, setInviteRole] = useState("");

  const [cancellingInvitation, setCancellingInvitation] = useState<MemberItem | null>(null);

  const [managedRole, setManagedRole] = useState<RoleItem | null>(null);

  const [memberSecurity, setMemberSecurity] = useState<{ mfa_enabled: boolean; last_access?: string; active_sessions: number; invitation_pending: boolean; credentials_configured: boolean } | null>(null);

  const [securityError, setSecurityError] = useState("");

  const [revision, setRevision] = useState(0);

  const [roleModalOpen, setRoleModalOpen] = useState(false);

  const [roleKey, setRoleKey] = useState("");

  const [roleTitle, setRoleTitle] = useState("");

  const [roleDescription, setRoleDescription] = useState("");

  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  const [permissionSearch, setPermissionSearch] = useState("");

  const [roleSearch] = useState("");

  const roleDisplay = "cards";

  const [rolePage, setRolePage] = useState(1);

  const [rolePageSize, setRolePageSize] = useState(6);

  const toast = useToast();

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      requestAllPages<{ items: Array<{ user_id: string; full_name: string; email: string; role: string; role_name: string; is_active: boolean; status: "active" | "invited" | "suspended" }> }>("/api/v1/users?page_size=100", "page"),
      transporte.solicitarDatos()
    ])
      .then(([usersResponse, rolesResponse]) => {
        if (!active) return;
        if (usersResponse.items) {
          setMembers((usersResponse.items || []).map((user) => ({ id: user.user_id, email: user.email, name: user.full_name || user.email.split("@")[0], role: user.role, role_name: user.role_name, is_active: user.is_active, status: user.is_active ? "active" : user.status || "invited" })));
        }
        if (rolesResponse.roles) {
          setRoles(rolesResponse.roles || []);
          setAllPermissions(rolesResponse.all_permissions || []);
          if (!inviteRole && rolesResponse.roles?.length) setInviteRole(rolesResponse.roles.find((role) => role.role !== "company_admin")?.role || rolesResponse.roles[0].role);
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
  }, [revision]);

  const handleOpenEditor = (member: MemberItem) => {
    setSelectedMember(member);
    setMemberSecurity(null);
    setSecurityError("");
    transporte.solicitarHandleOpenEditor({ member }).then(setMemberSecurity).catch(() => setSecurityError("No se pudo consultar la seguridad de este usuario."));
    setTargetRole(member.role);
    setEscalationError("");
  };

  const handleSaveRole = async (review: { reason: string; access_hash: string; acknowledge_responsibilities: boolean }) => {
    if (!selectedMember || !canWrite || saving) return;
    const currentPermissions = new Set(roles.find((role) => role.role === currentUserRole)?.permissions || []);
    const targetPermissions = roles.find((role) => role.role === targetRole)?.permissions || [];
    if (targetRole === "company_admin" && currentUserRole !== "company_admin" || targetPermissions.some((permission) => !currentPermissions.has(permission))) {
      setEscalationError(
        "No se puede elevar privilegios fuera de delegación. No puedes otorgar un rol o permisos con nivel superior al de tu propio usuario."
      );
      toast.error(
        "Escalada de privilegios bloqueada",
        "Control de seguridad RBAC: no puedes delegar privilegios que no posees."
      );
      return;
    }
    setSaving(true);
    try {
      await transporte.solicitarHandleSaveRole({ selectedMember, targetRole, review });
      setEscalationError("");
      const roleObj = roles.find((role) => role.role === targetRole);
      setMembers((prev) => prev.map((member) => member.id === selectedMember.id ? { ...member, role: targetRole, role_name: roleObj?.title || targetRole } : member));
      toast.success("Membresía actualizada", `El rol de ${selectedMember.name} fue actualizado a ${roleObj?.title || targetRole}.`);
      setSelectedMember(null);
    } catch (failure: unknown) {
      const detail = String((failure as { detail?: string }).detail || failure);
      setEscalationError(detail);
      toast.error("No se pudo actualizar la membresía", detail);
    } finally {
      setSaving(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canWrite || saving || !inviteEmail.trim() || !inviteRole) return;
    setSaving(true);
    try {
      const response = await transporte.solicitarHandleInvite({ inviteEmail, inviteRole });
      const roleObj = roles.find((role) => role.role === response.role);
      setMembers((current) => [{ id: response.user_id, email: response.email, name: response.email.split("@")[0], role: response.role, role_name: roleObj?.title || response.role, is_active: false, status: "invited" }, ...current]);
      toast.success("Invitación creada", `La invitación para ${inviteEmail} quedó en la bandeja de correo transaccional.`);
      setInviteEmail("");
      setInviteModalOpen(false);
    } catch (failure: unknown) {
      toast.error("No se pudo crear la invitación", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (member: MemberItem) => {
    if (!canWrite || saving) return;
    if (!await confirm({ title: member.is_active ? "¿Suspender usuario?" : "¿Reactivar usuario?", text: member.is_active ? "Se suspenderá al usuario y se cerrarán sus sesiones. Este cambio puede revertirse." : "Se reactivará el acceso del usuario. Este cambio puede revertirse.", danger: member.is_active, confirmLabel: member.is_active ? "Suspender" : "Reactivar" })) return;
    setSaving(true);
    try {
      const isActive = !member.is_active;
      await transporte.solicitarHandleToggleActive({ member, isActive });
      setMembers((current) => current.map((item) => item.id === member.id ? { ...item, is_active: isActive, status: isActive ? "active" : "suspended" } : item));
      toast.success(isActive ? "Usuario reactivado" : "Usuario suspendido", `${member.email} fue actualizado y sus sesiones vigentes fueron revocadas.`);
    } catch (failure: unknown) {
      toast.error("No se pudo cambiar el estado", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleResendInvitation = async (member: MemberItem) => {
    if (!canWrite || saving) return;
    setSaving(true);
    try {
      await transporte.solicitarHandleResendInvitation({ member });
      toast.success("Invitación reenviada", `Se generó un enlace nuevo y seguro para ${member.email}.`);
    } catch (failure: unknown) {
      toast.error("No se pudo reenviar la invitación", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const handleCancelInvitation = async () => {
    if (!cancellingInvitation || !canWrite || saving) return;
    setSaving(true);
    try {
      await transporte.solicitarHandleCancelInvitation({ cancellingInvitation });
      setMembers((current) => current.filter((item) => item.id !== cancellingInvitation.id));
      toast.success("Invitación cancelada", `El enlace enviado a ${cancellingInvitation.email} dejó de ser válido.`);
      setCancellingInvitation(null);
    } catch (failure: unknown) {
      toast.error("No se pudo cancelar la invitación", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };

  const permissionGroups = useMemo(() => {
    const query = permissionSearch.trim().toLowerCase();
    const visible = allPermissions.filter((permission) => {
      const label = permissionLabels[permission] || permission;
      return !query || permission.toLowerCase().includes(query) || label.toLowerCase().includes(query);
    });
    return visible.reduce<Record<string, string[]>>((groups, permission) => {
      const prefix = permission.split(":")[0];
      groups[prefix] = [...(groups[prefix] || []), permission];
      return groups;
    }, {});
  }, [allPermissions, permissionSearch]);

  const catalogRoles = useMemo(() => {
    const unique = new Map<string, RoleItem>();
    [...roles]
      .sort((left, right) => Number(Boolean(left.is_custom)) - Number(Boolean(right.is_custom)))
      .forEach((role) => {
        const normalizedTitle = role.title.trim().toLocaleLowerCase("es");
        if (!unique.has(normalizedTitle)) unique.set(normalizedTitle, role);
      });
    return [...unique.values()];
  }, [roles]);

  const filteredRoles = useMemo(() => {
    const query = roleSearch.trim().toLocaleLowerCase("es");
    return catalogRoles
      .filter((role) => !query || [role.title, role.role, role.description].some((value) => value.toLocaleLowerCase("es").includes(query)))
      .sort((left, right) => Number(Boolean(left.is_custom)) - Number(Boolean(right.is_custom)) || left.title.localeCompare(right.title, "es"));
  }, [catalogRoles, roleSearch]);

  const roleTotalPages = Math.max(1, Math.ceil(filteredRoles.length / rolePageSize));

  const visibleRoles = filteredRoles.slice((rolePage - 1) * rolePageSize, rolePage * rolePageSize);

  const roleRangeStart = filteredRoles.length ? (rolePage - 1) * rolePageSize + 1 : 0;

  const roleRangeEnd = Math.min(rolePage * rolePageSize, filteredRoles.length);

  useEffect(() => {
    setRolePage(1);
  }, [roleSearch, rolePageSize]);

  useEffect(() => {
    if (rolePage > roleTotalPages) setRolePage(roleTotalPages);
  }, [rolePage, roleTotalPages]);

  const roleKeyFromTitle = (value: string) => value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 64);

  const openRoleCreator = (source?: RoleItem) => {
    setRoleTitle(source ? `${source.title} personalizado` : "");
    setRoleKey("");
    setRoleDescription(source?.description || "");
    setSelectedPermissions(source?.permissions || []);
    setPermissionSearch("");
    setRoleModalOpen(true);
  };

  const togglePermission = (permission: string) => {
    setSelectedPermissions((current) => current.includes(permission) ? current.filter((item) => item !== permission) : [...current, permission]);
  };

  const handleCreateRole = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canWrite || saving || !roleKey || !roleTitle.trim()) return;
    setSaving(true);
    try {
      const created = await transporte.solicitarHandleCreateRole({ roleKey, roleTitle, roleDescription, selectedPermissions });
      setRoles((current) => [...current, { ...created, is_custom: true }]);
      setInviteRole(created.role);
      setRoleModalOpen(false);
      toast.success("Rol personalizado creado", `${created.title} ya puede asignarse a usuarios e invitaciones.`);
    } catch (failure: unknown) {
      toast.error("No se pudo crear el rol", String((failure as { detail?: string }).detail || failure));
    } finally {
      setSaving(false);
    }
  };
  return { ConfirmDialogNode, members, roles, allPermissions, workspaceView, setWorkspaceView, loading, loadError, selectedMember, setSelectedMember, targetRole, setTargetRole, escalationError, setEscalationError, inviteModalOpen, setInviteModalOpen, inviteEmail, setInviteEmail, inviteRole, setInviteRole, cancellingInvitation, setCancellingInvitation, managedRole, setManagedRole, memberSecurity, securityError, setRevision, roleModalOpen, setRoleModalOpen, roleKey, setRoleKey, roleTitle, setRoleTitle, roleDescription, setRoleDescription, selectedPermissions, setSelectedPermissions, permissionSearch, setPermissionSearch, roleDisplay, rolePage, setRolePage, rolePageSize, setRolePageSize, toast, saving, handleOpenEditor, handleSaveRole, handleInvite, handleToggleActive, handleResendInvitation, handleCancelInvitation, permissionGroups, catalogRoles, filteredRoles, roleTotalPages, visibleRoles, roleRangeStart, roleRangeEnd, roleKeyFromTitle, openRoleCreator, togglePermission, handleCreateRole };
}
