import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { DashboardAnalyticsTab } from "../../features/analitica/components/DashboardAnalyticsTab";

describe("ANA-001 a ANA-020: Dashboard Analytics Tab y Visualizacion Conectada", () => {
  it("renders the compact dashboard toolbar and filter panel", () => {
    const html = renderToString(
      <ToastProvider>
        <DashboardAnalyticsTab />
      </ToastProvider>
    );
    expect(html).toContain("dashboard-toolbar");
    expect(html).toContain("Últimos 30 días");
    expect(html).toContain("dashboard-filter-panel");
  });

  it("renders global filter selectors and active controls", () => {
    const html = renderToString(
      <ToastProvider>
        <DashboardAnalyticsTab />
      </ToastProvider>
    );
    expect(html).toContain("Filtrar resultados");
    expect(html).toContain("dash-period-select");
    expect(html).toContain("dash-currency-select");
    expect(html).toContain("Últimos 30 días");
    expect(html).toContain("Moneda base (");
  });

  it("renders action buttons for export, refresh and panels", () => {
    const html = renderToString(
      <ToastProvider>
        <DashboardAnalyticsTab />
      </ToastProvider>
    );
    expect(html).toContain("Refrescar");
    expect(html).toContain("Paneles");
    expect(html).toContain("Exportar CSV");
    expect(html).toContain("aria-busy");
  });

  it("contains accessible sections and data quality panel container", () => {
    const html = renderToString(
      <ToastProvider>
        <DashboardAnalyticsTab />
      </ToastProvider>
    );
    expect(html).toContain("Calidad y versiones del dataset");
    expect(html).toContain("section");
  });
});
