import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { CollaborationWorkspaceTab } from "../../features/trabajo/components/CollaborationWorkspaceTab";

describe("COL-001 a COL-014 / FAL-038 / REG-19: Collaboration Workspace Tab", () => {
  it("renders collaboration header and tabs", () => {
    const html = renderToString(
      <ToastProvider>
        <CollaborationWorkspaceTab />
      </ToastProvider>
    );
    expect(html).toContain("Notificaciones");
    expect(html).toContain("Tareas");
    expect(html).toContain("Aprobaciones");
    expect(html).toContain("Preferencias");
    expect(html).toContain("Vistas guardadas");
    expect(html).toContain("Ayuda contextual");
  });

  it("renders priority filter and notifications list container", () => {
    const html = renderToString(
      <ToastProvider>
        <CollaborationWorkspaceTab />
      </ToastProvider>
    );
    expect(html).toContain("Bandeja de notificaciones y alertas");
    expect(html).toContain("Filtrar prioridad:");
    expect(html).toContain("Todas");
    expect(html).toContain("Alta");
  });
});
