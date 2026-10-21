import { Children, cloneElement, createContext, isValidElement, useContext, type HTMLAttributes, type ReactNode } from "react";

const NavbarHeaderContext = createContext<string | null>(null);

const descriptions: Record<string, string> = {
  warranties: "Cobertura, diagnóstico, reparación y entrega de garantías.",
  records: "Relaciones, datos adicionales e historial de las operaciones.",
  payables: "Obligaciones, cuotas y pagos manuales a proveedores.",
  expenses: "Gastos, distribución y control de presupuestos internos.",
  work: "Tus tareas y actividad del día.",
  dashboard: "Resumen de ventas y resultados del negocio.",
  customers: "Contactos e historial comercial de tus clientes.",
  products: "Catálogo, precios y disponibilidad.",
  categories: "Organiza categorías y unidades de medida.",
  pricing: "Administra precios, descuentos y promociones.",
  quotations: "Prepara y gestiona tus cotizaciones.",
  orders: "Da seguimiento a los pedidos y entregas.",
  sales: "Documentos de venta y seguimiento de cobros.",
  team: "Vendedores y rendimiento del equipo comercial.",
  team_targets: "Objetivos por vendedor, equipo y empresa.",
  team_rules: "Condiciones, devengo y vigencia de las comisiones.",
  team_assignments: "Ventas compartidas y reemplazos temporales.",
  team_settlements: "Conciliación y liquidaciones por período y moneda.",
  inventory: "Existencias y movimientos de almacén.",
  receivables: "Saldos pendientes y vencimientos.",
  cash: "Apertura, seguimiento y cierre de sesiones de caja.",
  cash_movements: "Ingresos y egresos de la sesión seleccionada.",
  cash_counts: "Conteos físicos, revisión de diferencias y cierre.",
  cash_custody: "Fondos en custodia, entregas y recepción de transferencias.",
  cash_petty: "Anticipos, gastos sustentados y rendiciones.",
  cash_forecast: "Proyección de disponibilidad y compromisos de caja.",
  refunds: "Desembolsos y seguimiento de reembolsos.",
  refunds_settlements: "Aplicación del valor devuelto a deuda, cambios y saldos.",
  refunds_credit: "Orígenes y aplicaciones de saldos a favor por moneda.",
  settings_return_policy: "Condiciones, plazos y versiones de las políticas de devolución.",
  probability: "Escenarios e inferencia comercial.",
  reports: "Genera, consulta y exporta tus reportes.",
  collaboration: "Tareas y coordinación de tu equipo.",
  organization: "Empresa, sedes y almacenes.",
  security: "Sesiones y seguridad de tu cuenta.",
  sales_analytics: "Evolución y rendimiento de las ventas.",
  customer_analytics: "Comportamiento y segmentación de clientes.",
  datasets: "Calidad y versiones de tus datos.",
  variables: "Consulta las variables disponibles.",
  statistics: "Análisis y resúmenes estadísticos.",
  insights: "Hallazgos y oportunidades comerciales.",
  analytics_history: "Consulta y compara análisis anteriores.",
  audit: "Trazabilidad de cambios y operaciones.",
  notifications: "Avisos y novedades de tu actividad.",
  imports: "Carga y valida información del negocio.",
  users_roles: "Miembros, roles y permisos de acceso.",
  settings: "Datos fiscales y moneda de la empresa.",
  settings_branches: "Sedes, almacenes y ubicación de las operaciones.",
  settings_numbering: "Series y correlativos de documentos.",
  settings_rules: "Impuestos, crédito y políticas comerciales.",
  settings_profile: "Áreas y funciones habilitadas del negocio.",
  settings_functions: "Controles de aprobación y separación de responsabilidades.",
  settings_calendar: "Calendario y fechas de operación.",
  settings_branding: "Identidad visual y presentación de documentos.",
  settings_appearance: "Tema, accesibilidad y preferencias de la interfaz.",
  integrations: "Conecta y administra servicios externos.",
  approvals: "Revisa y resuelve solicitudes pendientes.",
  health: "Estado de servicios y diagnóstico.",
  profile_preferences: "Datos personales, seguridad y sesiones activas."
};

export function NavbarHeaderProvider({ view, children }: { view: string; children: ReactNode }) {
  return <NavbarHeaderContext.Provider value={view}>{children}</NavbarHeaderContext.Provider>;
}

export function NavbarHeaderSlot({ view, title }: { view: string; title: string }) {
  return <div className="navbar-section-slot">
    <h1 title={title}>{title}</h1>
    <p title={descriptions[view]}>{descriptions[view] || "Gestiona la información de este apartado."}</p>
  </div>;
}

function containsHeading(node: ReactNode): boolean {
  return Children.toArray(node).some(child => isValidElement<{ children?: ReactNode }>(child) && (
    (typeof child.type === "string" && /^h[1-3]$/.test(child.type)) || containsHeading(child.props.children)
  ));
}

function containsControl(node: ReactNode): boolean {
  return Children.toArray(node).some(child => isValidElement<{ children?: ReactNode; onClick?: unknown; onChange?: unknown }>(child) && (
    Boolean(child.props.onClick || child.props.onChange) || (typeof child.type === "string" && ["button", "input", "select", "a", "nav"].includes(child.type)) || containsControl(child.props.children)
  ));
}

function keepActions(node: ReactNode): ReactNode {
  return Children.map(node, child => {
    if (!isValidElement<{ children?: ReactNode }>(child) || !containsHeading(child)) return child;
    if (!containsControl(child)) return null;
    return cloneElement(child, undefined, keepActions(child.props.children));
  });
}

export function NavbarSectionHeader({ view, inline = false, children, ...props }: HTMLAttributes<HTMLElement> & { view?: string; inline?: boolean }) {
  const activeView = useContext(NavbarHeaderContext);
  if (!activeView || inline || (view && activeView !== view)) return <header {...props}>{children}</header>;
  const actions = keepActions(children);
  if (!containsControl(actions)) return null;
  return <div {...props} className="workspace-section-actions"><p className="workspace-actions-context">{descriptions[activeView]}</p>{actions}</div>;
}
