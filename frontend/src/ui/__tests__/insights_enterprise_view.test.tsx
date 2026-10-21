import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { InsightsEnterpriseView } from "../../features/insights/components/InsightsEnterpriseView";

const sampleInsights = [
  {
    id: "ins-1",
    title: "Margen bruto comprimido en Memoria RAM Enterprise",
    cifra_clave: "5.00%",
    period: "Catálogo activo",
    severity: "high" as const,
    status: "new" as const,
    observation: "Margen inferior al umbral",
    interpretation: "Se reduce la rentabilidad",
    suggested_action: "Revisar lista de precios",
    suggested_actions: [
      {
        action_id: "act-1",
        action_type: "price_adjustment",
        title: "Ajustar precio",
        description: "Ajustar margen a 15%",
        projected_impact: "+10% margen",
        requires_manual_confirmation: true,
        financial_auto_execution: false
      }
    ],
    cost_confidential: false
  }
];

function wrap(ui: React.ReactElement): string {
  return renderToString(<ToastProvider>{ui}</ToastProvider>);
}

describe("INS-009, INS-008, INS-011: InsightsEnterpriseView Vista Empresarial", () => {
  it("renders header, title, and F11 Enterprise badge", () => {
    const html = wrap(<InsightsEnterpriseView insights={sampleInsights} />);
    expect(html).toContain("Centro de Insights Determinísticos");
    expect(html).toContain("F11 Enterprise");
    expect(html).toContain("Marcar todos como leídos");
  });

  it("renders severity and status filter controls", () => {
    const html = wrap(<InsightsEnterpriseView insights={sampleInsights} />);
    expect(html).toContain("filter-severity");
    expect(html).toContain("filter-status");
    expect(html).toContain("Todas las gravedades");
    expect(html).toContain("Todos los estados");
  });

  it("renders insight card with key figure, period, severity, and novelty badge", () => {
    const html = wrap(<InsightsEnterpriseView insights={sampleInsights} />);
    expect(html).toContain("Margen bruto comprimido en Memoria RAM Enterprise");
    expect(html).toContain("5.00%");
    expect(html).toContain("Catálogo activo");
    expect(html).toContain("Gravedad: HIGH");
    expect(html).toContain("NOVEDAD");
    expect(html).toContain("motion-safe:animate-pulse");
  });

  it("renders evidence and draft action buttons with no financial auto execution", () => {
    const html = wrap(<InsightsEnterpriseView insights={sampleInsights} />);
    expect(html).toContain("Ver evidencia numérica");
    expect(html).toContain("Borrador de acción");
    expect(html).toContain("Observación:");
    expect(html).toContain("Interpretación:");
    expect(html).toContain("Acción recomendada:");
  });

  it("renders feedback buttons for calibration", () => {
    const html = wrap(<InsightsEnterpriseView insights={sampleInsights} />);
    expect(html).toContain("¿Útil?");
    expect(html).toContain("👍");
    expect(html).toContain("👎");
  });

  it("renders cost confidential state when redacted", () => {
    const confidentialInsight = [
      {
        id: "conf-1",
        title: "Alerta de rentabilidad comercial en Producto Confidencial",
        cifra_clave: "[RESTRINGIDO]",
        period: "Catálogo activo",
        severity: "high" as const,
        status: "new" as const,
        observation: "Se detecta desviación de rentabilidad comercial teórica sujeta a revisión administrativa.",
        interpretation: "Métricas de margen y costo confidenciales; no accesibles sin permiso.",
        suggested_action: "Contactar a un administrador o responsable de compras.",
        cost_confidential: true
      }
    ];
    const html = wrap(<InsightsEnterpriseView insights={confidentialInsight} />);
    expect(html).toContain("[RESTRINGIDO]");
    expect(html).toContain("Alerta de rentabilidad comercial en Producto Confidencial");
    expect(html).not.toContain("95.00 USD");
  });
});
