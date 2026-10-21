export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  event_type: string;
  priority: string;
  category: string;
  read: boolean;
  read_at?: string;
  created_at: string;
}

export interface PreferenceItem {
  category: string;
  channel: string;
  enabled: boolean;
  is_mandatory: boolean;
}

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: string;
  assignee_id?: string;
  assignee_active: boolean;
  inactive_assignee_warning: boolean;
  created_at: string;
}

export interface ApprovalItem {
  id: string;
  resource_type: string;
  resource_id: string;
  document_version: number;
  policy_name: string;
  status: string;
  requested_by: string;
}

export interface SavedViewItem {
  id: string;
  name: string;
  resource_type: string;
  schema_version: number;
  is_migrated: boolean;
  config: Record<string, unknown>;
}

export interface HelpArticleItem {
  screen: string;
  error_code?: string;
  title: string;
  content: string;
}
