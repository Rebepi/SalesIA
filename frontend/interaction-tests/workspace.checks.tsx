import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { IntegrationsWorkspaceTab } from "../src/features/integraciones/components/IntegrationsWorkspaceTab";
import { ApprovalsInboxWorkspaceTab } from "../src/features/aprobaciones/components/ApprovalsInboxWorkspaceTab";
import { UsersAndRolesWorkspaceTab } from "../src/features/seguridad/components/UsersAndRolesWorkspaceTab";
import { VariablesDictionaryTab } from "../src/features/analitica/components/VariablesDictionaryTab";
import { SystemHealthSupportWorkspaceTab } from "../src/features/soporte/components/SystemHealthSupportWorkspaceTab";
import { NotificationsWorkspaceTab } from "../src/features/notificaciones/components/NotificationsWorkspaceTab";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));

beforeEach(() => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ items: [] });
});
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("Workspace data and actions", () => {
  it("does not present demonstration integrations when the server is empty", async () => {
    render(<IntegrationsWorkspaceTab />);
    expect(screen.queryByText("Facturación Electrónica SUNAT / DIAN")).toBeNull();
    await screen.findByText("No hay conectores configurados para esta empresa.");
  });

  it("does not claim healthy services while the server cannot be reached", async () => {
    vi.mocked(apiClient.request).mockRejectedValue({ detail: "Servicio no disponible" });
    render(<SystemHealthSupportWorkspaceTab />);
    await screen.findByText("Servicio no disponible");
    expect(screen.queryByText("99.99%")).toBeNull();
    expect(screen.queryByText("PostgreSQL 16")).toBeNull();
  });

  it("loads real approval records and disables mutations while approval is pending", async () => {
    let resolve: (value: unknown) => void = () => {};
    vi.mocked(apiClient.request).mockImplementation(async (_path, options) => {
      if (options?.method === "POST") return new Promise(done => { resolve = done; });
      return { items: [{ id: "approval-real", code: "APR-REAL", requester_name: "Ana", requester_email: "ana@example.com", resource_type: "sale", resource_id: "sale-real", document_version: 2, policy_name: "Descuento", evidence: "Contrato validado", status: "pending", created_at: "2026-10-12T12:00:00Z" }] };
    });
    render(<ApprovalsInboxWorkspaceTab />);
    fireEvent.click(await screen.findByRole("button", { name: "Aprobar Solicitud" }));
    expect((screen.getByRole("button", { name: "Aprobar Solicitud" }) as HTMLButtonElement).disabled).toBe(true);
    resolve({});
    await screen.findByText("Aprobada");
    expect(apiClient.request).toHaveBeenCalledWith("/api/v1/collaboration/approvals/approval-real/decide", expect.objectContaining({ method: "POST" }));
  });

  it("keeps role actions unavailable in read-only mode", async () => {
    vi.mocked(apiClient.request).mockImplementation(async path => path.includes("/roles") ? { roles: [{ role: "sales_rep", title: "Vendedor", permissions: [] }] } : { items: [] });
    render(<UsersAndRolesWorkspaceTab canWrite={false} />);
    await waitFor(() => expect(apiClient.request).toHaveBeenCalledTimes(2));
    expect((screen.getByRole("button", { name: "Invitar Miembro" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByText("admin@empresa.com")).toBeNull();
  });

  it("loads fresh variables after returning to the section", async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({ items: [{ id: "real-var", name: "total", label: "Total real", scale: "quantitative_continuous", scale_label: "Continua", data_type: "decimal", source_table: "sales", description: "Importe", allowed_operations: ["Media"], sample_values: [], summary: { distinct_count: 1, null_count: 0 } }] }).mockResolvedValue({ items: [] });
    const view = render(<VariablesDictionaryTab />);
    await screen.findAllByText("Total real");
    expect(screen.queryByRole("button", { name: /Actualizar/i })).toBeNull();
    view.unmount();
    render(<VariablesDictionaryTab />);
    await waitFor(() => expect(screen.queryByText("Total real")).toBeNull());
  });

  it("never navigates to a notification resource when access is denied", async () => {
    const navigate = vi.fn();
    vi.mocked(apiClient.request).mockImplementation(async path => path.endsWith("/resource") ? { access_granted: false, resource_type: "sale", resource_id: "private-sale" } : { items: [{ id: "notice-real", title: "Aviso real", message: "Revisar documento", category: "Ventas", priority: "HIGH", read: false, resource_type: "sale", resource_id: "private-sale", created_at: "2026-10-12T12:00:00Z" }] });
    render(<NotificationsWorkspaceTab onNavigate={navigate} />);
    fireEvent.click(await screen.findByRole("button", { name: /Abrir recurso/ }));
    await screen.findByRole("alert");
    expect(navigate).not.toHaveBeenCalled();
  });
});
