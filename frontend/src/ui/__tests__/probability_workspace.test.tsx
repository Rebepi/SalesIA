import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { ProbabilityWorkspaceTab } from "../../features/analitica/components/ProbabilityWorkspaceTab";

const renderWithToast = (ui: React.ReactElement) => renderToString(<ToastProvider>{ui}</ToastProvider>);

describe("PROB-001 a PROB-016 y FAL-026: UI de Probabilidad Empírica y Bayes", () => {
  it("renders workspace title, description, and Kolmogorov badge", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Inferencia y Probabilidad Comercial");
    expect(html).toContain("Fase 09 · Motor Probabilístico");
    expect(html).toContain("Axiomas de Kolmogórov &amp; Bayes");
  });

  it("includes PROB-001 universe selector for customers and transactions", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Clientes Únicos (DISTINCT)");
    expect(html).toContain("Ventas (Transacciones)");
    expect(html).toContain("Tamaño del Universo n(Total)");
  });

  it("includes PROB-002 empirical count inputs for events A, B and intersection", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Recuento Evento A n(A)");
    expect(html).toContain("Recuento Evento B n(B)");
    expect(html).toContain("Intersección n(A ∩ B)");
    expect(html).toContain("Ejecutar Inferencia de Probabilidades");
  });

  it("includes PROB-006 preset button for README 1000/200/120/60 case", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Cargar Caso README (1,000 / 200 / 120 / 60)");
  });

  it("includes PROB-007 input mode switch between proportion and percentage", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Modo Empírico (Conteos Directos)");
    expect(html).toContain("Modo Manual (Parámetros Directos)");
    expect(html).toContain("Proporción [0, 1]");
    expect(html).toContain("Porcentaje [0, 100 %]");
  });

  it("includes PROB-011 Laplace smoothing toggle and alpha control", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Suavizado de Laplace");
  });

  it("includes PROB-015 persistence controls for saving analysis", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Persistencia de Análisis");
    expect(html).toContain("Nombre del análisis (ej. Retención Q3)");
  });

  it("includes FAL-026 hypothesis testing card with groups and action", () => {
    const html = renderWithToast(<ProbabilityWorkspaceTab />);
    expect(html).toContain("Semana 08 · Inferencia Avanzada");
    expect(html).toContain("Prueba de Hipótesis de Dos Proporciones");
    expect(html).toContain("Grupo 1 (A)");
    expect(html).toContain("Grupo 2 (B)");
    expect(html).toContain("Ejecutar Z-Test de Proporciones");
  });
});
