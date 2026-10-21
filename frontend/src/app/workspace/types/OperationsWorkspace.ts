export type Row = Record<string, string | number | boolean | null>;

export type View = "warranties" | "records" | "payables" | "expenses" | "work" | "dashboard" | "customers" | "products" | "categories" | "pricing" | "quotations" | "orders" | "sales" | "team" | "team_targets" | "team_rules" | "team_assignments" | "team_settlements" | "inventory" | "probability" | "reports" | "collaboration" | "organization" | "security" | "receivables" | "cash" | "cash_movements" | "cash_counts" | "cash_custody" | "cash_petty" | "cash_forecast" | "refunds" | "refunds_settlements" | "refunds_credit" | "refunds_policy" | "sales_analytics" | "customer_analytics" | "datasets" | "variables" | "statistics" | "insights" | "analytics_history" | "audit" | "notifications" | "imports" | "users_roles" | "settings" | "settings_branches" | "settings_numbering" | "settings_rules" | "settings_profile" | "settings_functions" | "settings_calendar" | "settings_branding" | "settings_appearance" | "settings_return_policy" | "integrations" | "approvals" | "health" | "profile_preferences";

export type Field = { name: string; label: string; type?: string; optional?: boolean; options?: { value: string; label: string }[]; value?: string };

export type Editor = { title: string; fields: Field[]; path: string; method?: string; values?: Record<string, unknown>; prepare?: (values: Record<string, string>) => unknown };
