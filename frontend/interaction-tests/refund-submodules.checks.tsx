import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { Panel1 as Sidebar } from "../src/app/workspace/sections/OperationsWorkspace/Panel1";
import { RefundsWorkspaceTab } from "../src/features/devoluciones/components/RefundsWorkspaceTab";
import { PaginatedTable } from "../src/ui/components/PaginatedTable";
import { apiClient } from "../src/api/client";
import { viewFromUrl } from "../src/app/workspace/support/OperationsWorkspace";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ error: vi.fn(), success: vi.fn(), warning: vi.fn() }) }));
vi.mock("../src/features/devoluciones/components/ReturnSettlementPanel", () => ({ ReturnSettlementPanel: ({ initialReturnId }: { initialReturnId: string }) => <section>Liquidación seleccionada: {initialReturnId}</section> }));
vi.mock("../src/features/devoluciones/components/CustomerCreditPanel", () => ({ CustomerCreditPanel: () => <section>Libro de créditos</section> }));
vi.mock("../src/features/devoluciones/components/ReturnPolicyPanel", () => ({ ReturnPolicyPanel: () => <section>Editor de políticas</section> }));
beforeEach(() => {
  vi.spyOn(apiClient, "request").mockResolvedValue([{ id: "refund-1", payment_id: "payment-1", return_id: "return-1", amount: "94.40", currency: "USD", reason: "Producto defectuoso", status: "confirmado", provider_reference: null, created_at: "2026-10-21" }] as never);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); window.history.replaceState({}, "", "/"); });

it("expone tres rutas y oculta el grupo sin permiso de consulta", () => {
  const navigate = vi.fn();
  const { rerender } = render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => true} view="refunds_settlements" navigate={navigate} />);
  const menu = screen.getByRole("list", { name: "Devoluciones y reembolsos" });
  for (const [label, key] of [["Reembolsos", "refunds"], ["Liquidación de devoluciones", "refunds_settlements"], ["Saldos a favor de clientes", "refunds_credit"]]) {
    fireEvent.click(within(menu).getByRole("button", { name: label }));
    expect(navigate).toHaveBeenLastCalledWith(key);
    window.history.replaceState({}, "", `/?view=${key}`);
    expect(viewFromUrl()).toBe(key);
  }
  rerender(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => false} view="dashboard" navigate={navigate} />);
  expect(screen.queryByRole("button", { name: "Devoluciones y reembolsos" })).toBeNull();
});

it("separa contenidos, conserva filtros y abre la liquidación vinculada", async () => {
  const navigate = vi.fn();
  const { rerender } = render(<RefundsWorkspaceTab section="refunds" onNavigate={navigate} />);
  await screen.findByText("Producto defectuoso");
  expect(screen.queryByText("Libro de créditos")).toBeNull();
  expect(screen.queryByText("Editor de políticas")).toBeNull();
  fireEvent.change(screen.getByRole("textbox", { name: "Buscar reembolso" }), { target: { value: "Producto" } });
  fireEvent.click(screen.getByRole("button", { name: "Ver liquidación vinculada" }));
  expect(navigate).toHaveBeenCalledWith("settlements");
  rerender(<RefundsWorkspaceTab section="settlements" onNavigate={navigate} />);
  expect(screen.getByText("Liquidación seleccionada: return-1")).toBeTruthy();
  expect(screen.queryByRole("region", { name: "Filtros de reembolsos" })).toBeNull();
  rerender(<RefundsWorkspaceTab section="credit" onNavigate={navigate} />);
  expect(screen.getByText("Libro de créditos")).toBeTruthy();
  expect(screen.queryByText("Liquidación seleccionada: return-1")).toBeNull();
  rerender(<RefundsWorkspaceTab section="refunds" onNavigate={navigate} />);
  expect((screen.getByRole("textbox", { name: "Buscar reembolso" }) as HTMLInputElement).value).toBe("Producto");
  await waitFor(() => expect(screen.getByRole("button", { name: "Gestionar reembolso" }).textContent).toBe(""));
});

it("no consulta la lista de reembolsos al entrar directamente a otro submódulo", () => {
  const { rerender } = render(<RefundsWorkspaceTab section="settlements" canWrite={false} />);
  expect(apiClient.request).not.toHaveBeenCalled();
  expect(screen.queryByTestId("request-refund-btn")).toBeNull();
  rerender(<RefundsWorkspaceTab section="credit" canWrite={false} />);
  expect(apiClient.request).not.toHaveBeenCalled();
});

it("comparte el colgroup entre encabezado y cuerpo para alinear las columnas", () => {
  const { container } = render(<PaginatedTable className="table-fixed"><colgroup><col style={{ width: "30%" }} /><col style={{ width: "70%" }} /></colgroup><thead><tr><th>ID</th><th>Motivo</th></tr></thead><tbody><tr><td>1</td><td>Prueba</td></tr></tbody></PaginatedTable>);
  const tables = container.querySelectorAll("table");
  expect(tables).toHaveLength(2);
  expect(tables[0].querySelector("colgroup")?.innerHTML).toBe(tables[1].querySelector("colgroup")?.innerHTML);
});
