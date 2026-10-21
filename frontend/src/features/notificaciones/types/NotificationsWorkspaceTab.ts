export interface SystemNotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  priority: string;
  read: boolean;
  resource_type?: string | null;
  resource_id?: string | null;
  created_at: string;
}

export interface NotificationsWorkspaceTabProps {
  canWrite?: boolean;
  compact?: boolean;
  refreshKey?: boolean;
  onUnreadCountChange?: (count: number) => void;
  userPermissions?: string[];
  onNavigate?: (view: string, resourceId?: string | null) => void;
}
