export interface UserSessionItem {
  session_id: string;
  device_name: string;
  ip_address: string;
  last_active: string;
  is_current: boolean;
}

export interface UserProfilePreferencesWorkspaceTabProps {
  canWrite?: boolean;
}
