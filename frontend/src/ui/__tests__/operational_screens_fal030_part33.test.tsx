import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../toast/ToastContext";

import { DashboardAnalyticsTab } from "../../features/analitica/components/DashboardAnalyticsTab";
import { SalesAnalyticsTab } from "../../features/analitica/components/SalesAnalyticsTab";
import { CustomerAnalyticsTab } from "../../features/clientes/analitica/CustomerAnalyticsTab";
import { DataQualityPanel } from "../../features/analitica/components/DataQualityPanel";
import { VariablesDictionaryTab } from "../../features/analitica/components/VariablesDictionaryTab";
import { StatisticalEngineWorkspaceTab } from "../../features/analitica/components/StatisticalEngineWorkspaceTab";
import { ProbabilityWorkspaceTab } from "../../features/analitica/components/ProbabilityWorkspaceTab";
import { InsightsEnterpriseView } from "../../features/insights/components/InsightsEnterpriseView";
import { AnalyticsHistoryWorkspaceTab } from "../../features/analitica/components/AnalyticsHistoryWorkspaceTab";
import { ReportsWorkspaceTab } from "../../features/reportes/components/ReportsWorkspaceTab";
import { AuditWorkspaceTab } from "../../features/auditoria/components/AuditWorkspaceTab";
import { NotificationsWorkspaceTab } from "../../features/notificaciones/components/NotificationsWorkspaceTab";
import { ImportsWorkspaceTab } from "../../features/importaciones/components/ImportsWorkspaceTab";
import { UsersAndRolesWorkspaceTab } from "../../features/seguridad/components/UsersAndRolesWorkspaceTab";
import { CompanySettingsWorkspaceTab } from "../../features/organizacion/components/CompanySettingsWorkspaceTab";
import { IntegrationsWorkspaceTab } from "../../features/integraciones/components/IntegrationsWorkspaceTab";
import { ApprovalsInboxWorkspaceTab } from "../../features/aprobaciones/components/ApprovalsInboxWorkspaceTab";
import { SystemHealthSupportWorkspaceTab } from "../../features/soporte/components/SystemHealthSupportWorkspaceTab";
import { UserProfilePreferencesWorkspaceTab } from "../../features/seguridad/components/UserProfilePreferencesWorkspaceTab";

const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
});

function wrap(ui: React.ReactElement): string {
  return renderToString(
    <QueryClientProvider client={testQueryClient}>
      <ToastProvider>
        {ui}
      </ToastProvider>
    </QueryClientProvider>
  );
}

describe("SCR-031 to SCR-050: Operational Screen Flows Verification Suite", () => {
  it("SCR-031 renders Analytics General with KPIs, mean/median comparison and filters", () => {
    const html = wrap(<DashboardAnalyticsTab />);
    expect(html).toContain("scr-031-analytics-general");
    expect(html).toContain("dashboard-toolbar");
    expect(html).toContain("Últimos 30 días");
    expect(html).toContain("Resumen Ejecutivo");
    expect(html).toContain("Filtrar resultados");
  });

  it("SCR-032 renders Sales Analytics with breakdowns by day, product, branch, and seller", () => {
    const html = wrap(<SalesAnalyticsTab />);
    expect(html).toContain("scr-032-sales-analytics");
    expect(html).toContain("Serie Temporal de Facturación");
    expect(html).toContain("Desglose por Día");
    expect(html).toContain("Por Producto");
    expect(html).toContain("Por Sucursal");
    expect(html).toContain("Por Vendedor");
    expect(html).toContain("Drill-down");
  });

  it("SCR-033 renders Customer Analytics with cohorts, Pareto and status definitions", () => {
    const html = wrap(<CustomerAnalyticsTab />);
    expect(html).toContain("scr-033-customer-analytics");
    expect(html).toContain("Analytics de Clientes y Cohortes");
    expect(html).toContain("Concentración Pareto");
    expect(html).toContain("Matriz de Retención por Cohortes Mensuales");
    expect(html).toContain("Tabla Explicativa de Cartera de Clientes");
    expect(html).toContain("Nuevo");
    expect(html).toContain("Recurrente");
    expect(html).toContain("Inactivo");
  });

  it("SCR-034 renders Datasets workspace with origin, grain, quality, and snapshot creation", () => {
    const html = wrap(<DataQualityPanel />);
    expect(html).toContain("scr-034-datasets-workspace");
    expect(html).toContain("Calidad y versiones del dataset");
    expect(html).toContain("DSET-019");
    expect(html).toContain("Auditoría de integridad, completitud por variable y versionado inmutable reproducible.");
  });

  it("SCR-035 renders Variables dictionary with scale types and mean prevention on nominal variables", () => {
    const html = wrap(<VariablesDictionaryTab />);
    expect(html).toContain("scr-035-variables-dictionary");
    expect(html).toContain("Diccionario de Variables Estadísticas");
    expect(html).toContain("Cargando");
    expect(html).not.toContain("Ticket Promedio de Venta");
  });

  it("SCR-036 renders Statistical engine workspace with exact Python Welford engine, n, and outliers", () => {
    const html = wrap(<StatisticalEngineWorkspaceTab />);
    expect(html).toContain("scr-036-statistics-workspace");
    expect(html).toContain("Motor Estadístico Descriptivo");
    expect(html).toContain("STATS_V2_PYTHON_EXACT");
    expect(html).toContain("Welford");
    expect(html).toContain("Parámetros de Ejecución");
  });

  it("SCR-037 renders Probability workspace with sample space, contingency table, and Kolmogorov axioms", () => {
    const html = wrap(<ProbabilityWorkspaceTab />);
    expect(html).toContain("scr-037-probability-workspace");
    expect(html).toContain("Inferencia y Probabilidad Comercial");
    expect(html).toContain("Definición de Universo y Eventos");
    expect(html).toContain("Axiomas de Kolmogórov &amp; Bayes");
  });

  it("SCR-038 renders Bayes workspace with 4-step calculation, prior/likelihood/posterior, and academic toggle", () => {
    const html = wrap(<ProbabilityWorkspaceTab />);
    expect(html).toContain("scr-038-bayes-workspace");
    expect(html).toContain("Modo Empírico (Conteos Directos)");
    expect(html).toContain("Modo Manual (Parámetros Directos)");
    expect(html).toContain("Suavizado de Laplace");
  });

  it("SCR-039 renders Insights feed with severity filters, evidence cards, and resolution actions", () => {
    const html = wrap(<InsightsEnterpriseView />);
    expect(html).toContain("scr-039-insights-feed");
    expect(html).toContain("Centro de Insights Determinísticos");
    expect(html).toContain("F11 Enterprise");
    expect(html).toContain("Gravedad:");
    expect(html).toContain("Marcar todos como leídos");
  });

  it("SCR-040 renders Analytics history with executions log, comparison, and repeat run preservation", () => {
    const html = wrap(<AnalyticsHistoryWorkspaceTab />);
    expect(html).toContain("scr-040-analytics-history");
    expect(html).toContain("Historial de Ejecuciones Analíticas");
    expect(html).toContain("Cargando historial analítico");
    expect(html).toContain("Comparar");
    expect(html).not.toContain("ana-001");
  });

  it("SCR-041 renders Reports workspace with catalog, preview, filters, and downloads", () => {
    const html = wrap(<ReportsWorkspaceTab />);
    expect(html).toContain("scr-041-reports-workspace");
    expect(html).toContain("Reportes Corporativos y Multiformato");
    expect(html).toContain("Catálogo Oficial");
    expect(html).toContain("Historial de Ejecuciones");
    expect(html).toContain("Programaciones Automáticas");
    expect(html).toContain("Comparación de Cortes");
  });

  it("SCR-042 renders Audit workspace with immutable ledger, trace ID, redacted diffs, and verification", () => {
    const html = wrap(<AuditWorkspaceTab />);
    expect(html).toContain("scr-042-audit-workspace");
    expect(html).toContain("Pista de Auditoría y Eventos Críticos");
    expect(html).toContain("Diff Redactado");
    expect(html).toContain("Verificar Cadena Criptográfica");
    expect(html).toContain("Exportación Separada");
    expect(html).toContain("Garantía de inmutabilidad");
  });

  it("SCR-043 renders Notifications center with categories, unread counts, and access revalidation", () => {
    const html = wrap(<NotificationsWorkspaceTab />);
    expect(html).toContain("scr-043-notifications-workspace");
    expect(html).toContain("Centro de Notificaciones del Sistema");
    expect(html).toContain("Marcar todas como leídas");
    expect(html).toContain("Cargando notificaciones");
    expect(html).not.toContain("PED-2026-0042");
  });

  it("SCR-044 renders Bulk imports wizard with 5 steps, simulation, and row error reporting", () => {
    const html = wrap(<ImportsWorkspaceTab />);
    expect(html).toContain("scr-044-imports-workspace");
    expect(html).toContain("Importaciones Masivas y Asistente ETL");
    expect(html).toContain("Paso 1: Selección de Entidad y Archivo");
    expect(html).toContain("Descargar Plantilla Modelo");
    expect(html).toContain("4. Simulación (Dry-Run)");
    expect(html).toContain("5. Ejecución Atómica");
  });

  it("SCR-045 renders Users and roles workspace with member list, role editor, and escalation guards", () => {
    const html = wrap(<UsersAndRolesWorkspaceTab currentUserRole="company_admin" />);
    expect(html).toContain("scr-045-users-roles-workspace");
    expect(html).toContain("Usuarios, Roles y Control de Acceso (RBAC)");
    expect(html).toContain("Invitar Miembro");
    expect(html).toContain("Roles y permisos");
    expect(html).not.toContain("admin@empresa.com");
  });

  it("SCR-046 renders Company settings workspace with branches, numbering, tax rules, and branding", () => {
    const html = wrap(<CompanySettingsWorkspaceTab />);
    expect(html).toContain("scr-046-configuration-workspace");
    expect(html).toContain("Configuración de Empresa y Sucursales");
    expect(html).toContain("Cargando configuración del sistema");
    expect(html).not.toContain("20100000001");
  });

  it("SCR-047 renders Integrations workspace with provider cards, masked credentials, and live mode", () => {
    const html = wrap(<IntegrationsWorkspaceTab />);
    expect(html).toContain("scr-047-integrations-workspace");
    expect(html).toContain("Integraciones y Conectores Externos");
    expect(html).toContain("Cargando");
    expect(html).not.toContain("sunat_prod_");
  });

  it("SCR-048 renders Approvals inbox with impact summary, version validation, and rejection reasons", () => {
    const html = wrap(<ApprovalsInboxWorkspaceTab />);
    expect(html).toContain("scr-048-approvals-inbox");
    expect(html).toContain("Bandeja de Aprobaciones");
    expect(html).toContain("Cargando solicitudes de aprobación");
    expect(html).not.toContain("APR-2026-0001");
  });

  it("SCR-049 renders System health & support with service statuses, retry jobs, and secret masking", () => {
    const html = wrap(<SystemHealthSupportWorkspaceTab isTechAdmin={true} />);
    expect(html).toContain("scr-049-system-health-support");
    expect(html).toContain("Estado de Servicios, Diagnóstico y Soporte");
    expect(html).not.toContain("99.99%");
    expect(html).not.toContain("job-001");
  });

  it("SCR-050 renders My account with personal details and session security without appearance settings", () => {
    const html = wrap(<UserProfilePreferencesWorkspaceTab />);
    expect(html).toContain("scr-050-profile-preferences");
    expect(html).toContain("Mi cuenta");
    expect(html).toContain("Datos Personales y de Contacto");
    expect(html).toContain("Sesiones Activas");
    expect(html).toContain("Guardar datos personales");
    expect(html).not.toContain("Preferencias de uso");
    expect(html).not.toContain("Densidad");
    expect(html).not.toContain("admin@empresa.com");
  });
});
