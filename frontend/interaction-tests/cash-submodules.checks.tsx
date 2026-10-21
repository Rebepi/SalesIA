import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Panel1 as Sidebar } from "../src/app/workspace/sections/OperationsWorkspace/Panel1";
import { CashRegisterWorkspaceTab } from "../src/features/caja/components/CashRegisterWorkspaceTab";
import { apiClient } from "../src/api/client";
import { viewFromUrl } from "../src/app/workspace/support/OperationsWorkspace";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ error: vi.fn(), success: vi.fn() }) }));
vi.mock("../src/features/caja/components/CashCustodyPanel", () => ({ CashCustodyPanel: () => <section>Panel de custodia</section> }));
vi.mock("../src/features/caja/components/PettyCashPanel", () => ({ PettyCashPanel: () => <section>Panel de caja chica</section> }));
vi.mock("../src/features/caja/components/CashForecastPanel", () => ({ CashForecastPanel: () => <section>Panel de proyección</section> }));

const session = (id: string) => ({ id, user_id: "u1", terminal_code: `TPV-${id}`, currency: "PEN", status: "open", opened_at: "2026-10-21", initial_cash: "100.00", expected_cash: "150.00", actual_cash: "150.00", difference_cash: "0", can_count: true, can_approve: true, control: { is_current: true, counted_cash: "150.00", version: 1, approval_status: "approved" }, movements: [{ movement_id: `m-${id}`, movement_type: "DEPOSIT", reason: `Ingreso ${id}`, amount: "50.00", balance_after: "150.00", timestamp: "2026-10-21T10:00:00" }] });

beforeEach(() => {
  vi.spyOn(apiClient, "getMe").mockResolvedValue({ user_id: "u1", permissions: [] } as never);
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (path === "/api/v1/cash-sessions") return [session("1"), session("2")] as never;
    if (path === "/api/v1/companies/current") return { base_currency: "PEN" } as never;
    return [] as never;
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); window.history.replaceState({}, "", "/"); });

it("despliega Caja y Arqueo con seis rutas y conserva el árbol comercial", () => {
  const navigate = vi.fn();
  render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => true} view="cash_counts" navigate={navigate} />);
  const menu = screen.getByRole("list", { name: "Caja y Arqueo" });
  const routes = [["Sesiones de caja", "cash"], ["Movimientos", "cash_movements"], ["Arqueos y diferencias", "cash_counts"], ["Custodia y transferencias", "cash_custody"], ["Caja chica y rendiciones", "cash_petty"], ["Proyección de caja", "cash_forecast"]];
  expect(within(menu).getByRole("button", { name: "Arqueos y diferencias" }).getAttribute("aria-current")).toBe("page");
  for (const [label, key] of routes) {
    fireEvent.click(within(menu).getByRole("button", { name: label }));
    expect(navigate).toHaveBeenLastCalledWith(key);
    window.history.replaceState({}, "", `/?view=${key}`);
    expect(viewFromUrl()).toBe(key);
  }
  fireEvent.click(screen.getByRole("button", { name: "Equipo y comisiones" }));
  expect(screen.getByRole("list", { name: "Equipo y comisiones" })).toBeTruthy();
});

it("oculta el grupo cuando falta el permiso de caja", () => {
  render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => false} view="dashboard" navigate={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Caja y Arqueo" })).toBeNull();
});

it("separa movimientos y arqueos, conserva sesión y cierra formularios al navegar", async () => {
  const { rerender, container } = render(<CashRegisterWorkspaceTab section="sessions" />);
  await screen.findByText("Terminal: TPV-1");
  expect(screen.queryByText("Movimientos de la Sesión")).toBeNull();
  const select = container.querySelector("select")!;
  fireEvent.change(select, { target: { value: "2" } });
  await screen.findByText("Terminal: TPV-2");
  fireEvent.click(screen.getByTestId("blind-count-btn"));
  expect(screen.getByText("Arqueo Ciego de Turno")).toBeTruthy();
  rerender(<CashRegisterWorkspaceTab section="movements" />);
  expect(screen.queryByText("Arqueo Ciego de Turno")).toBeNull();
  expect(screen.getByText("Ingreso 2")).toBeTruthy();
  expect(screen.queryByTestId("blind-count-btn")).toBeNull();
  expect(screen.getByTestId("add-movement-btn")).toBeTruthy();
  rerender(<CashRegisterWorkspaceTab section="counts" />);
  expect(screen.getByText("Terminal: TPV-2")).toBeTruthy();
  expect(screen.queryByText("Ingreso 2")).toBeNull();
  expect(screen.getByTestId("close-session-btn")).toBeTruthy();
  expect(screen.getByTestId("blind-count-btn")).toBeTruthy();
  expect(screen.queryByTestId("add-movement-btn")).toBeNull();
});

it("monta solo el panel solicitado sin consultar sesiones innecesarias", () => {
  const { rerender } = render(<CashRegisterWorkspaceTab section="custody" />);
  expect(screen.getByText("Panel de custodia")).toBeTruthy();
  expect(screen.queryByText("Panel de caja chica")).toBeNull();
  expect(apiClient.request).not.toHaveBeenCalled();
  rerender(<CashRegisterWorkspaceTab section="petty" />);
  expect(screen.getByText("Panel de caja chica")).toBeTruthy();
  expect(screen.queryByText("Panel de custodia")).toBeNull();
  rerender(<CashRegisterWorkspaceTab section="forecast" />);
  expect(screen.getByText("Panel de proyección")).toBeTruthy();
  expect(screen.queryByTestId("open-session-btn")).toBeNull();
});

it("mantiene la consulta de sesión sin acciones cuando no se permite operar", async () => {
  render(<CashRegisterWorkspaceTab section="counts" canWrite={false} />);
  await screen.findByText("Terminal: TPV-1");
  expect(screen.queryByTestId("blind-count-btn")).toBeNull();
  expect(screen.queryByTestId("close-session-btn")).toBeNull();
  expect(screen.queryByTestId("open-session-btn")).toBeNull();
});
