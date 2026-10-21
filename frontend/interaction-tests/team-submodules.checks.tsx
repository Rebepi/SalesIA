import { CommercialParticipationPanel } from "../src/features/equipo/components/CommercialParticipationPanel";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { Panel1 as Sidebar } from "../src/app/workspace/sections/OperationsWorkspace/Panel1";
import { SalesTeamTab } from "../src/features/equipo/components/SalesTeamTab";
import { apiClient } from "../src/api/client";
import { viewFromUrl } from "../src/app/workspace/support/OperationsWorkspace";
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ error: vi.fn(), success: vi.fn() }) }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
beforeEach(() => {
  vi.spyOn(apiClient, "getMe").mockResolvedValue({ permissions: ["sales:read"] } as never);
  vi.spyOn(apiClient, "request").mockImplementation(async (path: string) => {
    if (path === "/api/v1/companies/current") return { base_currency: "USD" } as never;
    if (path === "/api/v1/branches") return [] as never;
    return { items: [], total_count: 0 } as never;
  });
});
describe("Submódulos comerciales", () => {
  it("despliega el árbol y reconoce las cinco rutas", () => {
    const navigate = vi.fn();
    render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={() => true} view="dashboard" navigate={navigate} />);
    const parent = screen.getByRole("button", { name: "Equipo y comisiones" });
    expect(parent.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(parent);
    const menu = screen.getByRole("list", { name: "Equipo y comisiones" });
    for (const [label, view] of [["Equipo comercial", "team"], ["Metas", "team_targets"], ["Reglas de comisión", "team_rules"], ["Asignaciones y reemplazos", "team_assignments"], ["Liquidaciones", "team_settlements"]]) {
      fireEvent.click(within(menu).getByRole("button", { name: label }));
      expect(navigate).toHaveBeenLastCalledWith(view);
      window.history.replaceState({}, "", `/?view=${view}`);
      expect(viewFromUrl()).toBe(view);
    }
    fireEvent.click(parent);
    expect(screen.queryByRole("list", { name: "Equipo y comisiones" })).toBeNull();
  });
  it("resalta el hijo activo y oculta opciones sin permiso", () => {
    render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={permission => permission === "sales:read"} view="team_targets" navigate={vi.fn()} />);
    const menu = screen.getByRole("list", { name: "Equipo y comisiones" });
    expect(within(menu).getByRole("button", { name: "Metas" }).getAttribute("aria-current")).toBe("page");
    expect(within(menu).queryByRole("button", { name: "Reglas de comisión" })).toBeNull();
    expect(within(menu).queryByRole("button", { name: "Asignaciones y reemplazos" })).toBeNull();
    expect(within(menu).getAllByRole("button")).toHaveLength(3);
  });
  it("separa contenidos y conserva período y búsqueda al volver", async () => {
    const { rerender, container } = render(<SalesTeamTab section="team" />);
    await waitFor(() => expect(apiClient.request).toHaveBeenCalled());
    fireEvent.change(container.querySelector('input[type="month"]')!, { target: { value: "2026-09" } });
    fireEvent.change(screen.getByPlaceholderText("Buscar vendedor…"), { target: { value: "Ana" } });
    expect(screen.queryByText("Metas combinadas por vendedor, equipo y empresa")).toBeNull();
    rerender(<SalesTeamTab section="targets" />);
    await screen.findByRole("heading", { name: "Metas combinadas por vendedor, equipo y empresa" });
    expect(screen.queryByPlaceholderText("Buscar vendedor…")).toBeNull();
    expect(screen.queryByRole("heading", { name: "Conciliación y liquidaciones de comisiones por moneda" })).toBeNull();
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => String(path).startsWith("/api/v1/sales/commissions?"))).toBe(false);
    rerender(<SalesTeamTab section="settlements" />);
    await screen.findByRole("heading", { name: "Conciliación y liquidaciones de comisiones por moneda" });
    expect(screen.queryByRole("heading", { name: "Metas combinadas por vendedor, equipo y empresa" })).toBeNull();
    rerender(<SalesTeamTab section="team" />);
    expect((container.querySelector('input[type="month"]') as HTMLInputElement).value).toBe("2026-09");
    expect((screen.getByPlaceholderText("Buscar vendedor…") as HTMLInputElement).value).toBe("Ana");
  });
  it("bloquea reglas por URL directa cuando falta permiso de gestión", async () => {
    render(<SalesTeamTab section="rules" />);
    await screen.findByText("No tienes permiso para gestionar las reglas de comisión.");
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => String(path) === "/api/v1/sales/commission-policy")).toBe(false);
  });
  it("permite alternar ventas compartidas y reemplazos sin mezclar formularios", async () => {
    vi.mocked(apiClient.getMe).mockResolvedValue({ permissions: ["sales:read", "sales:write", "organization:manage"] } as never);
    vi.mocked(apiClient.request).mockImplementation(async (path: string) => {
      if (path === "/api/v1/companies/current") return { base_currency: "USD" } as never;
      if (path === "/api/v1/branches" || path === "/api/v1/sales/commission-coverages") return [] as never;
      return { items: [], total_count: 0 } as never;
    });
    render(<SalesTeamTab section="assignments" />);
    const shares = await screen.findByRole("button", { name: "Ventas compartidas" });
    const replacements = screen.getByRole("button", { name: "Reemplazos temporales" });
    expect(shares.getAttribute("aria-pressed")).toBe("true");
    expect(screen.queryByRole("button", { name: "Registrar reemplazo" })).toBeNull();
    fireEvent.click(replacements);
    expect(replacements.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: "Registrar reemplazo" })).toBeTruthy();
    fireEvent.click(shares);
    expect(screen.queryByRole("button", { name: "Registrar reemplazo" })).toBeNull();
  });
  it("busca vendedores por nombre sin tildes y conserva sus IDs en el formulario", async () => {
    vi.mocked(apiClient.request).mockImplementation(async (path: string) => {
      if (!path.includes("selector-options")) return [] as never;
      const query = new URL(path, "http://localhost").searchParams;
      const names = [{ value: "rep-jose", label: "José Pérez" }, { value: "rep-maria", label: "María Rojas" }];
      return { items: names.filter(row => query.get("ids") ? row.value === query.get("ids") : !query.get("search") || row.label.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().includes(query.get("search")!)), has_more: false } as never;
    });
    const reps = [{ rep_id: "rep-jose", full_name: "José Pérez" }, { rep_id: "rep-maria", full_name: "María Rojas" }] as never;
    render(<CommercialParticipationPanel reps={reps} canManage />);
    fireEvent.click(screen.getByRole("button", { name: "Reemplazos temporales" }));
    const absent = screen.getByRole("combobox", { name: /Vendedor ausente/ });
    fireEvent.click(absent);
    fireEvent.change(screen.getByRole("textbox", { name: "Buscar opciones" }), { target: { value: "jose" } });
    await screen.findByRole("option", { name: "José Pérez" });
    fireEvent.keyDown(screen.getByRole("textbox", { name: "Buscar opciones" }), { key: "Enter" });
    expect(screen.queryByRole("listbox")).toBeNull();
    const replacement = screen.getByRole("combobox", { name: /Reemplazo/ });
    fireEvent.click(replacement);
    fireEvent.change(screen.getByRole("textbox", { name: "Buscar opciones" }), { target: { value: "maria" } });
    fireEvent.click(await screen.findByRole("option", { name: "María Rojas" }));
    const form = screen.getByRole("button", { name: "Registrar reemplazo" }).closest("form")!;
    const values = new FormData(form);
    expect(values.get("representative_id")).toBe("rep-jose");
    expect(values.get("replacement_id")).toBe("rep-maria");
    expect(absent.classList.contains("custom-select-trigger")).toBe(true);
    await waitFor(() => expect(apiClient.request).toHaveBeenCalled());
  });
});
