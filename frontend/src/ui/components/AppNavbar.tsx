import { NavbarHeaderSlot } from "./NavbarSectionHeader";
import { NotificationBell } from "../../features/notificaciones/components/NotificationBell";
import { CustomSelect } from "./CustomSelect";
import { useEffect, useRef, useState } from "react";
import {
  Building2,
  ChevronDown,
  LogOut,
  Menu,
  Search,
  User,
  X,
} from "lucide-react";

export type NavView =
  | "warranties"
  | "records"
  | "payables"
  | "expenses"
  | "work"
  | "dashboard"
  | "customers"
  | "products"
  | "categories"
  | "pricing"
  | "quotations"
  | "orders"
  | "sales"
  | "team"
  | "inventory"
  | "probability"
  | "reports"
  | "collaboration"
  | "organization"
  | "security"
  | "receivables"
  | "cash"
  | "refunds"
  | "sales_analytics"
  | "customer_analytics"
  | "datasets"
  | "variables"
  | "statistics"
  | "insights"
  | "analytics_history"
  | "audit"
  | "notifications"
  | "imports"
  | "users_roles"
  | "settings"
  | "integrations"
  | "approvals"
  | "health"
  | "profile_preferences";

export interface AppNavbarProps {
  view: NavView;
  viewLabel: string;
  onNavigate: (v: NavView) => void;
  permissions?: string[];
  email: string;
  role: string;
  companyName: string;
  branches: Array<{ branch_id?: string; name?: string; code?: string; is_active?: boolean }>;
  activeBranchId: string;
  comparativeAllBranches?: boolean;
  onBranchChange: (id: string) => void;
  onOpenCompanySelector: () => void;
  onLogout: () => void;
  onOpenSearch?: () => void;
}

function useClickOutside(ref: React.RefObject<HTMLElement>, handler: () => void) {
  useEffect(() => {
    function listener(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        handler();
      }
    }
    document.addEventListener("mousedown", listener);
    return () => document.removeEventListener("mousedown", listener);
  }, [ref, handler]);
}

const ROLE_DISPLAY_NAMES: Record<string, string> = {
  company_admin: "Administrador de Empresa",
  manager: "Gerente Comercial",
  salesperson: "Vendedor",
  sales_rep: "Vendedor",
  seller: "Vendedor",
  analyst: "Analista de Datos",
  warehouse: "Responsable de Almacén",
  warehouse_keeper: "Responsable de Almacén",
  cashier: "Cajero / Finanzas",
  purchaser: "Encargado de Compras",
  auditor: "Auditor",
  platform_admin: "Administrador de Plataforma",
  customer_portal: "Portal de Clientes",
};

export function formatRoleLabel(roleName: string): string {
  if (!roleName) return "";
  return ROLE_DISPLAY_NAMES[roleName.toLowerCase()] || roleName.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export function AppNavbar({
  view,
  viewLabel,
  onNavigate,
  email,
  role,
  companyName,
  branches,
  activeBranchId,
  comparativeAllBranches = false,
  onBranchChange,
  onOpenCompanySelector,
  onLogout,
  onOpenSearch,
}: AppNavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const mobileRef = useRef<HTMLDivElement>(null!);
  const profileRef = useRef<HTMLDivElement>(null!);

  useClickOutside(mobileRef, () => setMobileOpen(false));
  useClickOutside(profileRef, () => setProfileOpen(false));

  const activeBranches = branches.filter(b => b.is_active !== false);

  const profileMenuItems: Array<{ key: NavView; label: string; Icon: React.ComponentType<{ className?: string }> }> = [
    { key: "profile_preferences", label: "Mi cuenta", Icon: User },
  ];

  return (
    <nav
      style={{
        background: "var(--sb-bg)",
        borderBottom: "1px solid var(--sb-border)",
        fontFamily: "'Inter', sans-serif",
      }}
      className="app-navbar sticky top-0 z-40 w-full"
      aria-label="Barra de navegación principal"
    >
      <div className="navbar-content flex h-16 items-center justify-between gap-3 px-4 lg:px-6">
        <div className="navbar-identity flex flex-1 items-center gap-3 min-w-0 mr-auto">
          <NavbarHeaderSlot view={view} title={viewLabel} />
          {onOpenSearch && <button type="button" onClick={onOpenSearch} title="Buscar en el sistema (Ctrl + K)" aria-label="Buscar en el sistema" className="ml-auto flex shrink-0 items-center gap-2 rounded-xl border border-white/20 p-2 text-xs text-white"><Search className="h-4 w-4" /><span className="hidden xl:inline">Buscar · Ctrl K</span></button>}
        </div>

        <div className="flex items-center gap-2 shrink-0">

          {companyName && (
            <button
              type="button"
              onClick={onOpenCompanySelector}
              title="Cambiar empresa"
              style={{
                color: "var(--sb-muted)",
                borderColor: "rgba(255,255,255,0.12)",
                background: "rgba(255,255,255,0.05)",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.10)";
                (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";
              }}
              className="hidden xl:flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[12px] font-medium transition-all duration-150"
            >
              <Building2 className="h-3.5 w-3.5 text-teal-400 shrink-0" />
              <span className="truncate max-w-[160px]">{companyName}</span>
            </button>
          )}

          {activeBranches.length >= 1 && (
            <label
              className="hidden md:flex navbar-branch-pill"
              htmlFor="navbar-branch-select"
            >
              <span className="text-[11px] shrink-0 opacity-80">
                {comparativeAllBranches ? "Sede operativa:" : "Sede:"}
              </span>
              <CustomSelect remote={{ resource: "branches", active_only: true }}
                id="navbar-branch-select"
                value={activeBranchId}
                onChange={e => onBranchChange(e.target.value)}
                style={{ background: "transparent", color: "var(--sb-text)" }}
                className="font-medium outline-none cursor-pointer max-w-[150px] text-[12px]"
              >
                {activeBranches.map(b => (
                  <option key={String(b.branch_id)} value={String(b.branch_id)}>
                    {String(b.name)} ({String(b.code)})
                  </option>
                ))}
              </CustomSelect>
            </label>
          )}

          <NotificationBell key={`${email}:${companyName}`} onNavigate={target => { setProfileOpen(false); setMobileOpen(false); onNavigate(target as NavView); }} />

          <div ref={profileRef} className="relative">
            <button
              type="button"
              onClick={() => setProfileOpen(prev => !prev)}
              aria-expanded={profileOpen}
              aria-haspopup="true"
              aria-label="Menú de usuario"
              style={{
                borderColor: "rgba(255,255,255,0.12)",
                background: profileOpen ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.05)",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.10)";
              }}
              onMouseLeave={e => {
                if (!profileOpen) {
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                }
              }}
              className="flex items-center gap-2 rounded-lg border pl-1.5 pr-2.5 py-1 transition-all duration-150"
            >
              <div
                style={{ background: "var(--sb-active)" }}
                className="flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold text-white uppercase shrink-0"
              >
                {email?.[0] ?? "U"}
              </div>
              <span style={{ color: "var(--sb-text)" }} className="hidden xl:block text-[12px] font-medium truncate max-w-[120px]">
                {email}
              </span>
              <ChevronDown
                style={{ color: "var(--sb-muted)" }}
                className={`h-3 w-3 transition-transform duration-200 ${profileOpen ? "rotate-180" : ""}`}
              />
            </button>

            {profileOpen && (
              <div
                style={{ background: "var(--sb-bg)", border: "1px solid var(--sb-border)" }}
                className="absolute right-0 top-full mt-2 w-60 rounded-2xl shadow-2xl shadow-black/40 overflow-hidden z-50"
              >
                <div style={{ borderBottom: "1px solid var(--sb-border)" }} className="px-4 py-3">
                  <p style={{ color: "var(--sb-text)" }} className="text-[13px] font-semibold truncate">
                    {email}
                  </p>
                  {role && (
                    <span className="inline-block mt-1.5 rounded-full border border-teal-700/50 bg-teal-900/40 px-2.5 py-0.5 text-[11px] font-medium tracking-wide text-teal-300">
                      {formatRoleLabel(role)}
                    </span>
                  )}
                </div>
                <ul className="p-1.5 space-y-0.5">
                  {profileMenuItems.map(({ key, label, Icon }) => {
                    const isActive = view === key;
                    return (
                      <li key={key}>
                        <button
                          type="button"
                          onClick={() => {
                            onNavigate(key);
                            setProfileOpen(false);
                          }}
                          style={{
                            color: isActive ? "var(--sb-text)" : "var(--sb-muted)",
                            background: isActive ? "var(--sb-hover)" : "transparent",
                          }}
                          onMouseEnter={e => {
                            if (!isActive) {
                              (e.currentTarget as HTMLElement).style.background = "var(--sb-hover)";
                              (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";
                            }
                          }}
                          onMouseLeave={e => {
                            if (!isActive) {
                              (e.currentTarget as HTMLElement).style.background = "transparent";
                              (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";
                            }
                          }}
                          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-100"
                        >
                          <Icon className="h-4 w-4 shrink-0" />
                          <span className="truncate flex-1 text-left">{label}</span>
                          {isActive && <span className="h-1.5 w-1.5 rounded-full bg-teal-300 shrink-0" />}
                        </button>
                      </li>
                    );
                  })}
                  {companyName && (
                    <li>
                      <button
                        type="button"
                        onClick={() => {
                          onOpenCompanySelector();
                          setProfileOpen(false);
                        }}
                        style={{ color: "var(--sb-muted)" }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLElement).style.background = "var(--sb-hover)";
                          (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLElement).style.background = "transparent";
                          (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";
                        }}
                        className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-100"
                      >
                        <Building2 className="h-4 w-4 shrink-0" />
                        <span className="truncate flex-1 text-left">Cambiar empresa</span>
                      </button>
                    </li>
                  )}
                </ul>
                <div style={{ borderTop: "1px solid var(--sb-border)" }} className="p-1.5">
                  <button
                    type="button"
                    onClick={onLogout}
                    className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] font-medium text-rose-400 transition-all duration-100 hover:bg-rose-950/40 hover:text-rose-300"
                  >
                    <LogOut className="h-4 w-4 shrink-0" />
                    <span className="truncate flex-1 text-left">Cerrar sesión</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setMobileOpen(prev => !prev)}
            aria-expanded={mobileOpen}
            aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
            style={{
              borderColor: "rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.05)",
              color: "var(--sb-muted)",
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.10)";
              (e.currentTarget as HTMLElement).style.color = "var(--sb-text)";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
              (e.currentTarget as HTMLElement).style.color = "var(--sb-muted)";
            }}
            className="md:hidden flex items-center justify-center h-8 w-8 rounded-lg border transition-all duration-150"
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div
          ref={mobileRef}
          style={{ borderTop: "1px solid var(--sb-border)" }}
          className="md:hidden max-h-[80vh] overflow-y-auto pb-4"
        >
          {viewLabel && (
            <div className="px-6 pt-4 pb-2 border-b" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
              <p style={{ color: "var(--sb-muted)" }} className="text-[10px] font-semibold uppercase tracking-widest leading-none">
                Espacio de trabajo
              </p>
              <p style={{ color: "var(--sb-text)" }} className="text-[14px] font-bold mt-1">
                {viewLabel}
              </p>
            </div>
          )}

          {companyName && (
            <div className="px-6 pt-3">
              <button
                type="button"
                onClick={() => {
                  onOpenCompanySelector();
                  setMobileOpen(false);
                }}
                style={{
                  color: "var(--sb-muted)",
                  borderColor: "rgba(255,255,255,0.12)",
                  background: "rgba(255,255,255,0.05)",
                }}
                className="w-full flex items-center gap-2 rounded-xl border px-3 py-2 text-[13px] font-medium"
              >
                <Building2 className="h-4 w-4 text-teal-400 shrink-0" />
                <span className="truncate flex-1 text-left">{companyName}</span>
              </button>
            </div>
          )}

          {activeBranches.length >= 1 && (
            <div className="px-6 pt-3">
              <label
                style={{ color: "var(--sb-muted)", letterSpacing: "0.08em" }}
                className="block text-[10px] font-semibold uppercase mb-1.5"
                htmlFor="mobile-branch-select"
              >
                Sede activa
              </label>
              <CustomSelect remote={{ resource: "branches", active_only: true }}
                id="mobile-branch-select"
                value={activeBranchId}
                onChange={e => onBranchChange(e.target.value)}
                style={{
                  background: "var(--sb-hover)",
                  color: "var(--sb-text)",
                  borderColor: "var(--sb-border)",
                }}
                className="w-full rounded-xl border px-3 py-2 text-[13px] font-medium outline-none"
              >
                {activeBranches.map(b => (
                  <option key={String(b.branch_id)} value={String(b.branch_id)}>
                    {String(b.name)} ({String(b.code)})
                  </option>
                ))}
              </CustomSelect>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
