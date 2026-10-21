import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { Panel1 as Sidebar } from "../src/app/workspace/sections/OperationsWorkspace/Panel1";
import { CompanySettingsWorkspaceTab } from "../src/features/organizacion/components/CompanySettingsWorkspaceTab";
import { useRefundsWorkspaceTab } from "../src/features/devoluciones/hooks/useRefundsWorkspaceTab";
import { apiClient } from "../src/api/client";
import { viewFromUrl } from "../src/app/workspace/support/OperationsWorkspace";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ error: vi.fn(), success: vi.fn(), warning: vi.fn() }) }));
vi.mock("../src/features/organizacion/components/OperatingProfileEditor", () => ({ OperatingProfileEditor: () => <div>Editor de áreas</div> }));
vi.mock("../src/features/organizacion/components/FunctionSeparationEditor", () => ({ FunctionSeparationEditor: () => <div>Editor de funciones</div> }));
vi.mock("../src/features/organizacion/components/OperatingCalendarEditor", () => ({ OperatingCalendarEditor: () => <div>Editor de calendario</div> }));
beforeEach(() => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (path === "/api/v1/companies/current") return { legal_name: "Empresa", trade_name: "Comercio", base_currency: "PEN" } as never;
    if (path === "/api/v1/companies/current/settings" || path === "/api/v1/auth/profile") return {} as never;
    return [] as never;
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); window.history.replaceState({}, "", "/"); });

it("expone diez submódulos de configuración con rutas propias y permisos", () => {
  const navigate = vi.fn();
  const { rerender } = render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => true} view="settings_calendar" navigate={navigate} />);
  const menu = screen.getByRole("list", { name: "Configuración" });
  expect(within(menu).getAllByRole("button")).toHaveLength(10);
  expect(within(menu).getByRole("button", { name: "Calendario operativo" }).getAttribute("aria-current")).toBe("page");
  fireEvent.click(within(menu).getByRole("button", { name: "Marca e impresión" }));
  expect(navigate).toHaveBeenLastCalledWith("settings_branding");
  for (const key of ["settings", "settings_branches", "settings_numbering", "settings_rules", "settings_profile", "settings_functions", "settings_calendar", "settings_branding", "settings_appearance"]) {
    window.history.replaceState({}, "", `/?view=${key}`);
    expect(viewFromUrl()).toBe(key);
  }
  rerender(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => false} view="dashboard" navigate={navigate} />);
  expect(screen.queryByRole("button", { name: "Configuración" })).toBeNull();
});

it("separa los editores y conserva el borrador de empresa entre submódulos", async () => {
  const { rerender } = render(<CompanySettingsWorkspaceTab section="company" />);
  const legalName = await screen.findByRole("textbox", { name: "Razón Social" });
  fireEvent.change(legalName, { target: { value: "Borrador conservado" } });
  rerender(<CompanySettingsWorkspaceTab section="profile" />);
  expect(screen.getByText("Editor de áreas")).toBeTruthy();
  expect(screen.queryByText("Editor de funciones")).toBeNull();
  expect(screen.queryByRole("navigation", { name: "Secciones de configuración" })).toBeNull();
  rerender(<CompanySettingsWorkspaceTab section="functions" />);
  expect(screen.getByText("Editor de funciones")).toBeTruthy();
  expect(screen.queryByText("Editor de áreas")).toBeNull();
  rerender(<CompanySettingsWorkspaceTab section="calendar" />);
  expect(screen.getByText("Editor de calendario")).toBeTruthy();
  rerender(<CompanySettingsWorkspaceTab section="company" canWrite={false} />);
  const input = screen.getByRole("textbox", { name: "Razón Social" }) as HTMLInputElement;
  expect(input.value).toBe("Borrador conservado");
  expect(input.disabled).toBe(true);
});

it("combina filtros en el servidor, busca con pausa y permite limpiarlos", async () => {
  const { result } = renderHook(() => useRefundsWorkspaceTab({ canWrite: false }));
  await waitFor(() => expect(result.current.loading).toBe(false));
  act(() => {
    result.current.setSelectedStatus("confirmado");
    result.current.setCurrencyFilter("USD");
    result.current.setDateFrom("2026-10-01");
    result.current.setDateTo("2026-10-21");
    result.current.setReturnFilter("false");
    result.current.setSearch("ajuste 10%");
  });
  await waitFor(() => expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => {
    const url = new URL(String(path), "http://localhost");
    return url.searchParams.get("search") === "ajuste 10%" && url.searchParams.get("currency") === "USD" && url.searchParams.get("status") === "confirmado" && url.searchParams.get("date_from") === "2026-10-01" && url.searchParams.get("date_to") === "2026-10-21" && url.searchParams.get("linked_return") === "false";
  })).toBe(true));
  act(() => result.current.resetFilters());
  await waitFor(() => expect(vi.mocked(apiClient.request).mock.calls.at(-1)?.[0]).toBe("/api/v1/refunds"));
  act(() => { result.current.setDateFrom("2026-11-01"); result.current.setDateTo("2026-10-01"); });
  await waitFor(() => expect(result.current.error).toContain("fecha inicial"));
  expect(result.current.filteredRefunds).toEqual([]);
});
