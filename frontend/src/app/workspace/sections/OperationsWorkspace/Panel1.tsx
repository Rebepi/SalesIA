import { useEffect, useState } from "react";
import { useOperatingProfile, viewAreas } from "../../../../features/organizacion/components/OperatingProfileContext";
import type { useOperationsWorkspace } from "../../hooks/useOperationsWorkspace";
import { ChevronDown } from "lucide-react";
import { sections } from "../../support/OperationsWorkspace";
import { sidebarGroups } from "../../support/OperationsWorkspace";

export function Panel1({ setSidebarHoveredTooltip, sidebarCollapsed, can, view, navigate }: { setSidebarHoveredTooltip: ReturnType<typeof useOperationsWorkspace>["setSidebarHoveredTooltip"]; sidebarCollapsed: ReturnType<typeof useOperationsWorkspace>["sidebarCollapsed"]; can: ReturnType<typeof useOperationsWorkspace>["can"]; view: ReturnType<typeof useOperationsWorkspace>["view"]; navigate: ReturnType<typeof useOperationsWorkspace>["navigate"] }) {
  const { enabled } = useOperatingProfile();
  const [showDisabled, setShowDisabled] = useState(false);
  const teamKeys = ["team", "team_targets", "team_rules", "team_assignments", "team_settlements"] as const;
  const cashKeys = ["cash", "cash_movements", "cash_counts", "cash_custody", "cash_petty", "cash_forecast"] as const;
  const cashActive = cashKeys.some(key => key === view);
  const [cashOpen, setCashOpen] = useState(cashActive);
  useEffect(() => { if (cashActive) setCashOpen(true); }, [view, cashActive]);
  const settingsKeys = ["settings", "settings_branches", "settings_numbering", "settings_rules", "settings_profile", "settings_functions", "settings_calendar", "settings_branding", "settings_appearance", "settings_return_policy"] as const;
  const settingsActive = settingsKeys.some(key => key === view);
  const [settingsOpen, setSettingsOpen] = useState(settingsActive);
  useEffect(() => { if (settingsActive) setSettingsOpen(true); }, [view, settingsActive]);
  const refundKeys = ["refunds", "refunds_settlements", "refunds_credit"] as const;
  const refundActive = refundKeys.some(key => key === view);
  const [refundOpen, setRefundOpen] = useState(refundActive);
  useEffect(() => { if (refundActive) setRefundOpen(true); }, [view, refundActive]);
  const teamActive = teamKeys.some(key => key === view);
  const [teamOpen, setTeamOpen] = useState(teamActive);
  useEffect(() => { if (teamActive) setTeamOpen(true); }, [view, teamActive]);
  return (<nav

    aria-label="Menú principal"

    onScroll={() => setSidebarHoveredTooltip(null)}

    style={{ overscrollBehavior: "contain" }}

    className={sidebarCollapsed ? "flex-1 overflow-y-auto px-2 py-4 space-y-4 overscroll-contain" : "flex-1 overflow-y-auto px-3 py-4 space-y-5 overscroll-contain"}

  >

    <button type="button" onClick={() => setShowDisabled(value => !value)} className="mb-2 rounded p-2 text-[10px] text-slate-500" aria-pressed={showDisabled}>{showDisabled ? "Ocultar áreas desactivadas" : sidebarCollapsed ? "Historial" : "Mostrar áreas desactivadas (historial)"}</button>

    {sidebarGroups.map(group => {

      const visibleItems = group.items

        .map(key => sections.find(s => s.key === key))

        .filter((s): s is typeof sections[number] => !!s && (!s.permission || can(s.permission) || (s.key === "settings" && can("payments:read"))) && (showDisabled || !viewAreas[s.key] || enabled(viewAreas[s.key])));

      if (visibleItems.length === 0) return null;

      return (

        <div key={group.title}>

          {sidebarCollapsed ? (

            <div className="my-2 mx-auto w-6 border-t" style={{ borderColor: "var(--sb-border)" }} />

          ) : (

            <p

              style={{ color: "var(--sb-muted)", letterSpacing: "0.08em" }}

              className="mb-1.5 px-2 text-[10px] font-semibold uppercase"

            >

              {group.title}

            </p>

          )}

          <ul className="space-y-1">

            {visibleItems.map(({ key, label, Icon }) => {

              if (key === "team") {
                const children = teamKeys.map(child => sections.find(item => item.key === child)!).filter(item => !item.permission || can(item.permission));
                return <li key={key}>
                  <button type="button" aria-label="Equipo y comisiones" aria-expanded={teamOpen} aria-controls="team-submenu" onClick={() => setTeamOpen(value => !value)}
                    className={sidebarCollapsed ? "mx-auto flex h-10 w-10 items-center justify-center rounded-xl" : "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[13px] font-medium"}
                    style={{ color: teamActive ? "var(--sb-text)" : "var(--sb-muted)", background: teamActive ? "var(--sb-hover)" : undefined }}
                    onMouseEnter={event => { if (sidebarCollapsed) { const rect = event.currentTarget.getBoundingClientRect(); setSidebarHoveredTooltip({ label: "Equipo y comisiones", top: rect.top + rect.height / 2 }); } }}
                    onMouseLeave={() => setSidebarHoveredTooltip(null)}>
                    <Icon className="h-4 w-4 shrink-0" />{!sidebarCollapsed && <><span className="flex-1">Equipo y comisiones</span><ChevronDown className={`h-4 w-4 transition-transform ${teamOpen ? "rotate-180" : ""}`} /></>}
                  </button>
                  {teamOpen && <ul id="team-submenu" aria-label="Equipo y comisiones" className={sidebarCollapsed ? "mt-1 space-y-1" : "ml-5 mt-1 space-y-1 border-l pl-2"} style={{ borderColor: "var(--sb-border)" }}>
                    {children.map(child => <li key={child.key}><button type="button" title={sidebarCollapsed ? child.label : undefined} aria-label={child.label} aria-current={view === child.key ? "page" : undefined} onClick={() => navigate(child.key)}
                      className={sidebarCollapsed ? "mx-auto flex h-9 w-10 items-center justify-center rounded-lg text-xs" : "w-full rounded-lg px-3 py-2 text-left text-xs font-medium"}
                      style={{ background: view === child.key ? "var(--sb-hover)" : undefined, color: view === child.key ? "var(--sb-active)" : "var(--sb-muted)" }}>
                      {sidebarCollapsed ? <child.Icon className="h-4 w-4" /> : child.label}
                    </button></li>)}
                  </ul>}
                </li>;
              }
              if (key === "cash") {
                const children = cashKeys.map(child => sections.find(item => item.key === child)!).filter(item => !item.permission || can(item.permission));
                return <li key={key}>
                  <button type="button" aria-label="Caja y Arqueo" aria-expanded={cashOpen} aria-controls="cash-submenu" onClick={() => setCashOpen(value => !value)}
                    className={sidebarCollapsed ? "mx-auto flex h-10 w-10 items-center justify-center rounded-xl" : "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[13px] font-medium"}
                    style={{ color: cashActive ? "var(--sb-text)" : "var(--sb-muted)", background: cashActive ? "var(--sb-hover)" : undefined }}
                    onMouseEnter={event => { if (sidebarCollapsed) { const rect = event.currentTarget.getBoundingClientRect(); setSidebarHoveredTooltip({ label: "Caja y Arqueo", top: rect.top + rect.height / 2 }); } }}
                    onMouseLeave={() => setSidebarHoveredTooltip(null)}>
                    <Icon className="h-4 w-4 shrink-0" />{!sidebarCollapsed && <><span className="flex-1">Caja y Arqueo</span><ChevronDown className={`h-4 w-4 transition-transform ${cashOpen ? "rotate-180" : ""}`} /></>}
                  </button>
                  {cashOpen && <ul id="cash-submenu" aria-label="Caja y Arqueo" className={sidebarCollapsed ? "mt-1 space-y-1" : "ml-5 mt-1 space-y-1 border-l pl-2"} style={{ borderColor: "var(--sb-border)" }}>
                    {children.map(child => <li key={child.key}><button type="button" title={sidebarCollapsed ? child.label : undefined} aria-label={child.label} aria-current={view === child.key ? "page" : undefined} onClick={() => navigate(child.key)}
                      className={sidebarCollapsed ? "mx-auto flex h-9 w-10 items-center justify-center rounded-lg text-xs" : "w-full rounded-lg px-3 py-2 text-left text-xs font-medium"}
                      style={{ background: view === child.key ? "var(--sb-hover)" : undefined, color: view === child.key ? "var(--sb-active)" : "var(--sb-muted)" }}>
                      {sidebarCollapsed ? <child.Icon className="h-4 w-4" /> : child.label}
                    </button></li>)}
                  </ul>}
                </li>;
              }
              if (key === "settings") {
                const children = settingsKeys.map(child => sections.find(item => item.key === child)!).filter(item => !item.permission || can(item.permission));
                return <li key={key}>
                  <button type="button" aria-label="Configuración" aria-expanded={settingsOpen} aria-controls="settings-submenu" onClick={() => setSettingsOpen(value => !value)}
                    className={sidebarCollapsed ? "mx-auto flex h-10 w-10 items-center justify-center rounded-xl" : "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[13px] font-medium"}
                    style={{ color: settingsActive ? "var(--sb-text)" : "var(--sb-muted)", background: settingsActive ? "var(--sb-hover)" : undefined }}
                    onMouseEnter={event => { if (sidebarCollapsed) { const rect = event.currentTarget.getBoundingClientRect(); setSidebarHoveredTooltip({ label: "Configuración", top: rect.top + rect.height / 2 }); } }}
                    onMouseLeave={() => setSidebarHoveredTooltip(null)}>
                    <Icon className="h-4 w-4 shrink-0" />{!sidebarCollapsed && <><span className="flex-1">Configuración</span><ChevronDown className={`h-4 w-4 transition-transform ${settingsOpen ? "rotate-180" : ""}`} /></>}
                  </button>
                  {settingsOpen && <ul id="settings-submenu" aria-label="Configuración" className={sidebarCollapsed ? "mt-1 space-y-1" : "ml-5 mt-1 space-y-1 border-l pl-2"} style={{ borderColor: "var(--sb-border)" }}>
                    {children.map(child => <li key={child.key}><button type="button" title={sidebarCollapsed ? child.label : undefined} aria-label={child.label} aria-current={view === child.key ? "page" : undefined} onClick={() => navigate(child.key)}
                      className={sidebarCollapsed ? "mx-auto flex h-9 w-10 items-center justify-center rounded-lg text-xs" : "w-full rounded-lg px-3 py-2 text-left text-xs font-medium"}
                      style={{ background: view === child.key ? "var(--sb-hover)" : undefined, color: view === child.key ? "var(--sb-active)" : "var(--sb-muted)" }}>
                      {sidebarCollapsed ? <child.Icon className="h-4 w-4" /> : child.label}
                    </button></li>)}
                  </ul>}
                </li>;
              }
              if (key === "refunds") {
                const children = refundKeys.map(child => sections.find(item => item.key === child)!).filter(item => !item.permission || can(item.permission));
                return <li key={key}>
                  <button type="button" aria-label="Devoluciones y reembolsos" aria-expanded={refundOpen} aria-controls="refund-submenu" onClick={() => setRefundOpen(value => !value)}
                    className={sidebarCollapsed ? "mx-auto flex h-10 w-10 items-center justify-center rounded-xl" : "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-[13px] font-medium"}
                    style={{ color: refundActive ? "var(--sb-text)" : "var(--sb-muted)", background: refundActive ? "var(--sb-hover)" : undefined }}
                    onMouseEnter={event => { if (sidebarCollapsed) { const rect = event.currentTarget.getBoundingClientRect(); setSidebarHoveredTooltip({ label: "Devoluciones y reembolsos", top: rect.top + rect.height / 2 }); } }}
                    onMouseLeave={() => setSidebarHoveredTooltip(null)}>
                    <Icon className="h-4 w-4 shrink-0" />{!sidebarCollapsed && <><span className="flex-1">Devoluciones y reembolsos</span><ChevronDown className={`h-4 w-4 transition-transform ${refundOpen ? "rotate-180" : ""}`} /></>}
                  </button>
                  {refundOpen && <ul id="refund-submenu" aria-label="Devoluciones y reembolsos" className={sidebarCollapsed ? "mt-1 space-y-1" : "ml-5 mt-1 space-y-1 border-l pl-2"} style={{ borderColor: "var(--sb-border)" }}>
                    {children.map(child => <li key={child.key}><button type="button" title={sidebarCollapsed ? child.label : undefined} aria-label={child.label} aria-current={view === child.key ? "page" : undefined} onClick={() => navigate(child.key)}
                      className={sidebarCollapsed ? "mx-auto flex h-9 w-10 items-center justify-center rounded-lg text-xs" : "w-full rounded-lg px-3 py-2 text-left text-xs font-medium"}
                      style={{ background: view === child.key ? "var(--sb-hover)" : undefined, color: view === child.key ? "var(--sb-active)" : "var(--sb-muted)" }}>
                      {sidebarCollapsed ? <child.Icon className="h-4 w-4" /> : child.label}
                    </button></li>)}
                  </ul>}
                </li>;
              }
              const isActive = view === key;

              return (

                <li key={key}>

                  <button

                    onClick={() => navigate(key)}

                    aria-current={isActive ? "page" : undefined}

                    aria-label={label}

                    style={

                      isActive

                        ? {

                          background: "var(--sb-hover)",

                          color: "var(--sb-text)",

                          borderLeft: sidebarCollapsed ? "none" : "3px solid var(--sb-active)",

                        }

                        : {

                          color: "var(--sb-muted)",

                          borderLeft: sidebarCollapsed ? "none" : "3px solid transparent",

                        }

                    }

                    className={

                      sidebarCollapsed

                        ? "relative flex h-10 w-10 mx-auto items-center justify-center rounded-xl transition-all duration-150 focus-visible:outline focus-visible:outline-2"

                        : "group flex w-full items-center gap-3 rounded-r-lg px-3 py-2 text-left text-[13px] font-medium transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"

                    }

                    onMouseEnter={e => {

                      if (!isActive) {

                        (e.currentTarget as HTMLButtonElement).style.background = "var(--sb-hover)";

                        (e.currentTarget as HTMLButtonElement).style.color = "var(--sb-text)";

                      }

                      if (sidebarCollapsed) {

                        const rect = e.currentTarget.getBoundingClientRect();

                        setSidebarHoveredTooltip({ label, top: rect.top + rect.height / 2 });

                      }

                    }}

                    onMouseLeave={e => {

                      if (!isActive) {

                        (e.currentTarget as HTMLButtonElement).style.background = "";

                        (e.currentTarget as HTMLButtonElement).style.color = "var(--sb-muted)";

                      }

                      if (sidebarCollapsed) {

                        setSidebarHoveredTooltip(null);

                      }

                    }}

                  >

                    <Icon className={sidebarCollapsed ? "h-5 w-5 shrink-0" : "h-4 w-4 shrink-0"} />

                    {!sidebarCollapsed && <span className="truncate">{label}</span>}

                    {sidebarCollapsed && isActive && (

                      <span className="absolute left-1 top-1/2 -translate-y-1/2 h-2 w-1 rounded-full bg-teal-400" />

                    )}

                  </button>

                </li>

              );

            })}

          </ul>

        </div>

      );

    })}

  </nav>);
}
