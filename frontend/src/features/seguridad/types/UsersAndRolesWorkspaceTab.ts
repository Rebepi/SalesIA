export interface MemberItem {
  id: string;
  email: string;
  name: string;
  role: string;
  role_name: string;
  is_active: boolean;
  status: "active" | "suspended" | "invited";
  branches?: string[];
  last_login?: string;
}

export interface RoleItem {
  role: string;
  title: string;
  description: string;
  permissions: string[];
  is_custom?: boolean;
}

export interface UsersAndRolesWorkspaceTabProps {
  canWrite?: boolean;
  currentUserRole?: string;
}
