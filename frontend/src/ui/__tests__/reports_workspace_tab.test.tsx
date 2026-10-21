import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { ReportsWorkspaceTab } from "../../features/reportes/components/ReportsWorkspaceTab";

describe("RPT-001 a RPT-022 / FAL-029 / REG-18: Reports Workspace Tab", () => {
  it("renders reports workspace header, branding and description", () => {
    const html = renderToString(
      <ToastProvider>
        <ReportsWorkspaceTab />
      </ToastProvider>
    );
    expect(html).toContain("Reportes Corporativos y Multiformato");
    expect(html).toContain("Catálogo oficial certificado");
    expect(html).toContain("sellado criptográfico");
    expect(html).not.toContain(">Actualizar</button>");
  });

  it("renders navigation tabs for catalog, runs, schedules, and compare", () => {
    const html = renderToString(
      <ToastProvider>
        <ReportsWorkspaceTab />
      </ToastProvider>
    );
    expect(html).toContain("Catálogo Oficial");
    expect(html).toContain("Historial de Ejecuciones");
    expect(html).toContain("Programaciones Automáticas");
    expect(html).toContain("Comparación de Cortes");
  });

  it("renders catalog search input and area filter buttons", () => {
    const html = renderToString(
      <ToastProvider>
        <ReportsWorkspaceTab />
      </ToastProvider>
    );
    expect(html).toContain("Buscar reporte por código o nombre...");
    expect(html).toContain("Todas las áreas");
    expect(html).toContain("Ventas");
    expect(html).toContain("Analítica");
    expect(html).toContain("Clientes");
    expect(html).toContain("Inventario");
    expect(html).toContain("Finanzas");
  });
});
