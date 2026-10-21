import { lazy, ReactNode, useEffect, useId, useRef } from "react";
import { Activity, Award, BarChart2, BarChart3, Bell, BookOpen, Briefcase, Building2, Check, ClipboardList, Database, DollarSign, FileSpreadsheet, FileText, FolderTree, Globe, History, LayoutDashboard, Package, RotateCcw, Server, Settings, ShieldCheck, ShoppingCart, Sparkles, Tag, Upload, User, UserCheck, Users, Wallet, X } from "lucide-react";
import { BayesProbabilityIcon } from "../../../ui/icons/index";
import { View } from "../types/OperationsWorkspace";

export const ReportsWorkspaceTab = lazy(() => import("../../../features/reportes/components/ReportsWorkspaceTab").then(module => ({ default: module.ReportsWorkspaceTab })));

export const InventoryWorkspaceTab = lazy(() => import("../../../features/inventario/components/InventoryWorkspaceTab").then(module => ({ default: module.InventoryWorkspaceTab })));

export const ImportsWorkspaceTab = lazy(() => import("../../../features/importaciones/components/ImportsWorkspaceTab").then((m) => ({ default: m.ImportsWorkspaceTab })));

export const UsersAndRolesWorkspaceTab = lazy(() => import("../../../features/seguridad/components/UsersAndRolesWorkspaceTab").then((m) => ({ default: m.UsersAndRolesWorkspaceTab })));

export const CompanySettingsWorkspaceTab = lazy(() => import("../../../features/organizacion/components/CompanySettingsWorkspaceTab").then((m) => ({ default: m.CompanySettingsWorkspaceTab })));

export const IntegrationsWorkspaceTab = lazy(() => import("../../../features/integraciones/components/IntegrationsWorkspaceTab").then((m) => ({ default: m.IntegrationsWorkspaceTab })));

export const ApprovalsInboxWorkspaceTab = lazy(() => import("../../../features/aprobaciones/components/ApprovalsInboxWorkspaceTab").then((m) => ({ default: m.ApprovalsInboxWorkspaceTab })));

export const SystemHealthSupportWorkspaceTab = lazy(() => import("../../../features/soporte/components/SystemHealthSupportWorkspaceTab").then((m) => ({ default: m.SystemHealthSupportWorkspaceTab })));

export const UserProfilePreferencesWorkspaceTab = lazy(() => import("../../../features/seguridad/components/UserProfilePreferencesWorkspaceTab").then((m) => ({ default: m.UserProfilePreferencesWorkspaceTab })));

export const TabFallback = () => <div className="flex h-48 items-center justify-center text-sm text-slate-400">Cargando módulo…</div>;

export const inputStyle = "mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100";

export const primaryButtonStyle = "group inline-flex items-center justify-center gap-2 rounded-xl bg-teal-600 hover:bg-teal-500 active:bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-teal-900/30 transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-40";

export const buttonStyle = "group inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 dark:border-slate-600/70 bg-white dark:bg-slate-700/80 hover:bg-slate-50 dark:hover:bg-slate-600/80 hover:border-slate-300 dark:hover:border-slate-500 px-3.5 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 shadow-xs transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-40";

export const actionViewStyle = "inline-flex h-8 w-8 items-center justify-center rounded-lg border border-sky-200 dark:border-slate-600/70 bg-sky-50 dark:bg-slate-700/80 text-sky-600 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-sky-500/20 hover:border-sky-300 dark:hover:border-sky-500/50 hover:text-sky-700 dark:hover:text-sky-300 transition active:scale-90 shadow-2xs";

export const actionEditStyle = "inline-flex h-8 w-8 items-center justify-center rounded-lg border border-amber-200 dark:border-slate-600/70 bg-amber-50 dark:bg-slate-700/80 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-500/20 hover:border-amber-300 dark:hover:border-amber-500/50 hover:text-amber-700 dark:hover:text-amber-300 transition active:scale-90 shadow-2xs";

export const actionDeleteStyle = "inline-flex h-8 w-8 items-center justify-center rounded-lg border border-rose-200 dark:border-slate-600/70 bg-rose-50 dark:bg-slate-700/80 text-rose-600 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-500/20 hover:border-rose-300 dark:hover:border-rose-500/50 hover:text-rose-700 dark:hover:text-rose-300 transition active:scale-90 shadow-2xs";

export const actionTextStyle = "group inline-flex items-center justify-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold shadow-2xs transition active:scale-95 disabled:opacity-40";

export const iconStyle = "h-4 w-4 motion-safe:transition-transform motion-safe:group-hover:scale-110 motion-safe:group-focus-visible:scale-110";

export const iconStyleSm = "h-3.5 w-3.5";

export const viewKeys = new Set<View>(["warranties", "records", "payables", "expenses", "work", "dashboard", "customers", "products", "categories", "pricing", "quotations", "orders", "sales", "team", "team_targets", "team_rules", "team_assignments", "team_settlements", "inventory", "probability", "reports", "collaboration", "organization", "security", "receivables", "cash", "cash_movements", "cash_counts", "cash_custody", "cash_petty", "cash_forecast", "refunds", "refunds_settlements", "refunds_credit", "refunds_policy", "sales_analytics", "customer_analytics", "datasets", "variables", "statistics", "insights", "analytics_history", "audit", "notifications", "imports", "users_roles", "settings", "settings_branches", "settings_numbering", "settings_rules", "settings_profile", "settings_functions", "settings_calendar", "settings_branding", "settings_appearance", "settings_return_policy", "integrations", "approvals", "health", "profile_preferences"]);

export function viewFromUrl(): View {

  if (typeof window === "undefined") return "dashboard";

  const requested = new URLSearchParams(window.location.search).get("view") as View | null;

  if (requested === "refunds_policy") return "settings_return_policy";
  return requested && viewKeys.has(requested) ? requested : "dashboard";

}

export const sections = [

  { key: "warranties" as View, label: "Garantías", Icon: ShieldCheck, permission: "sales:read" },

  { key: "records" as View, label: "Expedientes y campos", Icon: BookOpen, permission: "" },

  { key: "payables" as View, label: "Cuentas por pagar", Icon: Wallet, permission: "payments:read" },

  { key: "expenses" as View, label: "Gastos y presupuestos", Icon: DollarSign, permission: "payments:read" },

  { key: "work" as View, label: "Mi trabajo", Icon: Briefcase, permission: "" },

  { key: "dashboard" as View, label: "Inicio ejecutivo", Icon: LayoutDashboard, permission: "analytics:dataset:read" },

  { key: "customers" as View, label: "Clientes", Icon: Users, permission: "customers:read" },

  { key: "products" as View, label: "Productos", Icon: Package, permission: "products:read" },

  { key: "categories" as View, label: "Categorías y unidades", Icon: FolderTree, permission: "products:read" },

  { key: "pricing" as View, label: "Precios y promociones", Icon: Tag, permission: "products:read" },

  { key: "quotations" as View, label: "Cotizaciones", Icon: FileText, permission: "sales:read" },

  { key: "orders" as View, label: "Pedidos", Icon: ClipboardList, permission: "sales:read" },

  { key: "sales" as View, label: "Ventas y cobros", Icon: ShoppingCart, permission: "sales:read" },

  { key: "team" as View, label: "Equipo comercial", Icon: Award, permission: "sales:read" },
  { key: "team_targets" as View, label: "Metas", Icon: Award, permission: "sales:read" },
  { key: "team_rules" as View, label: "Reglas de comisión", Icon: Award, permission: "organization:manage" },
  { key: "team_assignments" as View, label: "Asignaciones y reemplazos", Icon: Users, permission: "sales:write" },
  { key: "team_settlements" as View, label: "Liquidaciones", Icon: Wallet, permission: "sales:read" },

  { key: "inventory" as View, label: "Inventario", Icon: Activity, permission: "inventory:read" },

  { key: "receivables" as View, label: "Cuentas por cobrar", Icon: DollarSign, permission: "payments:read" },

  { key: "cash" as View, label: "Sesiones de caja", Icon: Wallet, permission: "cash:register:manage" },
  { key: "cash_movements" as View, label: "Movimientos", Icon: Wallet, permission: "cash:register:manage" },
  { key: "cash_counts" as View, label: "Arqueos y diferencias", Icon: Wallet, permission: "cash:register:manage" },
  { key: "cash_custody" as View, label: "Custodia y transferencias", Icon: Wallet, permission: "cash:register:manage" },
  { key: "cash_petty" as View, label: "Caja chica y rendiciones", Icon: Wallet, permission: "cash:register:manage" },
  { key: "cash_forecast" as View, label: "Proyección de caja", Icon: Wallet, permission: "cash:register:manage" },

  { key: "refunds" as View, label: "Reembolsos", Icon: RotateCcw, permission: "payments:read" },
  { key: "refunds_settlements" as View, label: "Liquidación de devoluciones", Icon: RotateCcw, permission: "payments:read" },
  { key: "refunds_credit" as View, label: "Saldos a favor de clientes", Icon: RotateCcw, permission: "payments:read" },
  { key: "settings_return_policy" as View, label: "Políticas de devolución", Icon: Settings, permission: "payments:read" },

  { key: "probability" as View, label: "Probabilidad y Bayes", Icon: BayesProbabilityIcon, permission: "analytics:dataset:read" },

  { key: "reports" as View, label: "Reportes", Icon: FileSpreadsheet, permission: "reports:read" },

  { key: "collaboration" as View, label: "Colaboración", Icon: Bell, permission: "" },

  { key: "organization" as View, label: "Organización", Icon: Building2, permission: "organization:manage" },

  { key: "sales_analytics" as View, label: "Analytics Ventas", Icon: BarChart3, permission: "analytics:dataset:read" },

  { key: "customer_analytics" as View, label: "Analytics Clientes", Icon: Users, permission: "analytics:dataset:read" },

  { key: "datasets" as View, label: "Datasets", Icon: Database, permission: "analytics:dataset:read" },

  { key: "variables" as View, label: "Variables", Icon: BookOpen, permission: "analytics:dataset:read" },

  { key: "statistics" as View, label: "Estadística", Icon: BarChart2, permission: "analytics:dataset:read" },

  { key: "insights" as View, label: "Insights", Icon: Sparkles, permission: "analytics:dataset:read" },

  { key: "analytics_history" as View, label: "Historial Analítico", Icon: History, permission: "analytics:dataset:read" },

  { key: "audit" as View, label: "Pista de Auditoría", Icon: ShieldCheck, permission: "audit:logs:read" },

  { key: "imports" as View, label: "Importaciones", Icon: Upload, permission: "imports:write" },

  { key: "users_roles" as View, label: "Usuarios y Roles", Icon: UserCheck, permission: "users:manage" },

  { key: "settings" as View, label: "Empresa", Icon: Settings, permission: "organization:manage" },
  { key: "settings_branches" as View, label: "Sedes y almacenes", Icon: Settings, permission: "organization:manage" },
  { key: "settings_numbering" as View, label: "Series y correlativos", Icon: Settings, permission: "organization:manage" },
  { key: "settings_rules" as View, label: "Políticas comerciales y fiscales", Icon: Settings, permission: "organization:manage" },
  { key: "settings_profile" as View, label: "Áreas del negocio", Icon: Settings, permission: "organization:manage" },
  { key: "settings_functions" as View, label: "Separación de funciones", Icon: Settings, permission: "organization:manage" },
  { key: "settings_calendar" as View, label: "Calendario operativo", Icon: Settings, permission: "organization:manage" },
  { key: "settings_branding" as View, label: "Marca e impresión", Icon: Settings, permission: "organization:manage" },
  { key: "settings_appearance" as View, label: "Apariencia", Icon: Settings, permission: "organization:manage" },

  { key: "integrations" as View, label: "Integraciones", Icon: Globe, permission: "operations:manage" },

  { key: "approvals" as View, label: "Aprobaciones", Icon: Check, permission: "approvals:manage" },

  { key: "health" as View, label: "Estado y Soporte", Icon: Server, permission: "" },

  { key: "profile_preferences" as View, label: "Mi cuenta", Icon: User, permission: "" }

];

export function isModuleAuthorized(permission: string, permissions: string[]) {

  return permission === "imports:write"

    ? permissions.some(item => ["customers:write", "products:write", "inventory:write"].includes(item))

    : !permission || permissions.includes(permission);

}

export const sidebarGroups = [

  {

    title: "PRINCIPAL",

    items: ["work", "dashboard", "records"] as View[],

  },

  {

    title: "COMERCIAL",

    items: ["customers", "products", "categories", "pricing", "quotations", "orders", "sales", "warranties", "team"] as View[],

  },

  {

    title: "FINANZAS",

    items: ["inventory", "receivables", "payables", "expenses", "cash", "refunds", "reports"] as View[],

  },

  {

    title: "ANALYTICS",

    items: ["sales_analytics", "customer_analytics", "datasets", "variables", "statistics", "probability", "insights", "analytics_history"] as View[],

  },

  {

    title: "ADMINISTRACIÓN",

    items: ["collaboration", "organization", "approvals", "imports", "users_roles", "settings", "integrations", "audit", "health"] as View[],

  },

];

export function message(error: unknown) {

  if (error && typeof error === "object" && "detail" in error) {

    if (typeof error.detail === "string") return error.detail;

    if (error.detail && typeof error.detail === "object" && "title" in error.detail) return String(error.detail.title);

  }

  return "No se pudo completar la operación. Revisa la conexión y vuelve a intentar.";

}

export function Dialog({ title, children, close, id }: { title: string; children: ReactNode; close: () => void; id?: string }) {

  const generatedId = useId();

  const dialogId = id || `dialog-${generatedId.replace(/:/g, "")}`;

  const element = useRef<HTMLDialogElement>(null);

  useEffect(() => {

    const previous = document.activeElement as HTMLElement | null;

    element.current?.showModal();

    return () => { previous?.focus(); };

  }, []);

  return <dialog ref={element} onCancel={close} aria-labelledby={`${dialogId}-title`} className="max-h-[90vh] w-[min(94vw,620px)] rounded-2xl border-0 bg-white p-0 shadow-2xl backdrop:bg-slate-950/60"><header className="flex items-center justify-between border-b border-slate-100 p-6"><h2 id={`${dialogId}-title`} className="text-xl font-semibold text-slate-900">{title}</h2><button type="button" onClick={close} className={buttonStyle} aria-label="Cerrar"><X className={iconStyle} /></button></header>{children}</dialog>;

}
