import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { FinancialManagementWorkspace } from "../src/features/finanzas/components/FinancialManagementWorkspace";

vi.mock("../src/features/finanzas/components/SupplierCreditLedger", () => ({ SupplierCreditLedger: () => <section>Saldos a favor</section> }));
vi.mock("../src/features/compras/components/SupplierClaimsPanel", () => ({ SupplierClaimsPanel: () => <section>Reclamos</section> }));
afterEach(cleanup);

it("conserva la paginación del servidor y el acceso de solo lectura", async () => {
  const request = vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).startsWith("/api/v1/payables?")) return { items: [{ id: "p1", document_number: "PROV-01", supplier_name: "Proveedor", currency: "PEN", amount: "100.00", balance: "100.00", status: "open", due_date: "2026-11-01" }], total_count: 26, balances_by_currency: { PEN: "2600.00" } } as never;
    return [] as never;
  });
  render(<FinancialManagementWorkspace mode="payables" permissions={["payments:read"]} />);
  await screen.findByText("PROV-01");
  expect(screen.queryByRole("heading", { name: "Cuentas por pagar" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Nueva obligación" })).toBeNull();
  expect(screen.getByRole("button", { name: "Ver cuotas y pagos" }).textContent).toBe("");
  expect(screen.getByRole("button", { name: "Siguiente" }).closest(".payables-pagination")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
  await waitFor(() => expect(request).toHaveBeenCalledWith("/api/v1/payables?limit=25&offset=25"));
  expect(screen.getByText("Saldos a favor")).toBeTruthy();
  expect(screen.getByText("Reclamos")).toBeTruthy();
});

it("muestra el vacío y las acciones de creación según permisos", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).startsWith("/api/v1/payables?")) return { items: [], total_count: 0, balances_by_currency: {} } as never;
    if (path === "/api/v1/payable-options") return { suppliers: [], purchase_orders: [], invoice_matches: [] } as never;
    return [] as never;
  });
  render(<FinancialManagementWorkspace mode="payables" permissions={["payments:read", "payments:write"]} />);
  await screen.findByText("Todavía no hay registros.");
  expect(screen.getByRole("button", { name: "Nueva obligación" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Anticipo o crédito" })).toBeTruthy();
  expect((screen.getByRole("button", { name: "Siguiente" }) as HTMLButtonElement).disabled).toBe(true);
});

it("presenta gastos, presupuestos y centros sin alterar sus importes", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).startsWith("/api/v1/expenses?")) return { items: [{ id: "e1", title: "Alquiler", category: "Local", expense_date: "2026-10-21", currency: "PEN", amount: "500.00", status: "draft", version: 1, created_by: "u1", allocations: [{ cost_center_id: "c1", amount: "500.00" }] }], total_count: 1 } as never;
    if (path === "/api/v1/cost-centers") return [{ id: "c1", code: "ADM", name: "Administración" }] as never;
    if (path === "/api/v1/cost-budgets") return [{ id: "b1", cost_center_id: "c1", period: "2026-10", currency: "PEN", amount: "1000.00", consumed: "500.00", remaining: "500.00", version: 1 }] as never;
    return [] as never;
  });
  render(<FinancialManagementWorkspace mode="expenses" permissions={["payments:write", "organization:manage"]} userId="u1" />);
  await screen.findByText("Alquiler");
  expect(screen.queryByRole("heading", { name: "Gastos, centros de costo y presupuestos" })).toBeNull();
  expect(screen.getByRole("button", { name: "Enviar gasto a aprobación" }).textContent).toBe("");
  expect(screen.getByRole("button", { name: "Cancelar gasto" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Nuevo centro" })).toBeTruthy();
  expect(screen.getByText("Presupuesto: PEN 1000.00")).toBeTruthy();
  expect(screen.getByText("Administración").closest(".financial-center")).toBeTruthy();
});

it("respeta la aprobación independiente y la lectura sin acciones de escritura", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).startsWith("/api/v1/expenses?")) return { items: [{ id: "e2", title: "Servicios", category: "Local", expense_date: "2026-10-21", currency: "PEN", amount: "50.00", status: "pending", version: 1, created_by: "u1", allocations: [] }], total_count: 1 } as never;
    return [] as never;
  });
  const { rerender } = render(<FinancialManagementWorkspace mode="expenses" permissions={["payments:write", "approvals:manage"]} userId="u1" />);
  await screen.findByText("Servicios");
  expect(screen.queryByRole("button", { name: "Aprobar gasto" })).toBeNull();
  rerender(<FinancialManagementWorkspace mode="expenses" permissions={["payments:write", "approvals:manage"]} userId="u2" />);
  expect(screen.getByRole("button", { name: "Aprobar gasto" }).textContent).toBe("");
  expect(screen.getByRole("button", { name: "Rechazar gasto" })).toBeTruthy();
  rerender(<FinancialManagementWorkspace mode="expenses" permissions={["payments:read"]} userId="u2" />);
  expect(screen.queryByRole("button", { name: "Aprobar gasto" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Nuevo gasto" })).toBeNull();
});
