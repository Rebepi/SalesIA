import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { CashCustodyPanel } from "../src/features/caja/components/CashCustodyPanel";
import { PettyCashPanel } from "../src/features/caja/components/PettyCashPanel";
import { CashForecastPanel } from "../src/features/caja/components/CashForecastPanel";

beforeEach(() => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (path === "/api/v1/cash-custody/options") return { accounts: [], endpoints: [], people: [], branches: [], current_user_id: "u1", can_configure: true, base_currency: "PEN" } as never;
    if (String(path).startsWith("/api/v1/cash-custody/transfers?")) return { items: [], total_count: 0, in_transit_by_currency: {} } as never;
    if (path === "/api/v1/petty-cash/options") return { funds: [], accounts: [], people: [], current_user_id: "u1", can_review: true, cost_centers: [], business_date: "2026-10-21" } as never;
    if (String(path).startsWith("/api/v1/petty-cash/advances?")) return { items: [], total_count: 0 } as never;
    if (path === "/api/v1/cash-forecast/preview") return { business_date: "2026-10-21", end_date: "2026-11-19", points: [], items: [], timelines: [], warnings: [], stale_source_keys: [], in_transit_by_currency: {}, method: "Criterios del cálculo", generated_at: "2026-10-21T10:00:00" } as never;
    return [] as never;
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("custodia conserva filtros de servidor y permisos de configuración", async () => {
  const { rerender } = render(<CashCustodyPanel canWrite revision={0} onChanged={vi.fn()} />);
  await screen.findByRole("button", { name: "Nuevo punto de custodia" });
  expect(screen.getByRole("button", { name: "Entregar efectivo" }).className).toContain("cash-button-primary");
  const status = screen.getByRole("combobox", { name: "Estado" });
  fireEvent.click(status);
  fireEvent.click(screen.getByRole("option", { name: "Recibido" }));
  await waitFor(() => expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => String(path).includes("status=received"))).toBe(true));
  expect(screen.getByRole("button", { name: "Siguiente" }).closest(".cash-submodule-pagination")).toBeTruthy();
  rerender(<CashCustodyPanel canWrite={false} revision={0} onChanged={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Entregar efectivo" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Nuevo punto de custodia" })).toBeNull();
});

it("caja chica mantiene formularios y restricciones de escritura", async () => {
  const { rerender } = render(<PettyCashPanel canWrite revision={0} onChanged={vi.fn()} />);
  await screen.findByRole("button", { name: "Configurar fondo" });
  fireEvent.click(screen.getByRole("button", { name: "Configurar fondo" }));
  expect(screen.getByRole("heading", { name: "Reglas del fondo" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Siguiente" }).closest(".cash-submodule-pagination")).toBeTruthy();
  rerender(<PettyCashPanel canWrite={false} revision={0} onChanged={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Solicitar anticipo" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Configurar fondo" })).toBeNull();
});

it("proyección conserva el cálculo y ofrece escenarios con el selector propio", async () => {
  render(<CashForecastPanel canWrite={false} revision={0} />);
  await screen.findByText(/Desde 2026-10-21 hasta 2026-11-19/);
  expect(screen.getByRole("combobox", { name: "Escenario" })).toBeTruthy();
  expect(screen.queryByText("Nombre del escenario")).toBeNull();
  const before = vi.mocked(apiClient.request).mock.calls.filter(([path]) => path === "/api/v1/cash-forecast/preview").length;
  fireEvent.click(screen.getByRole("button", { name: "Calcular con datos actuales" }));
  await waitFor(() => expect(vi.mocked(apiClient.request).mock.calls.filter(([path]) => path === "/api/v1/cash-forecast/preview").length).toBeGreaterThan(before));
});

function mockForecastDocuments() {
  const items = Array.from({ length: 65 }, (_, index) => ({ key: `source-${index}`, title: `Cobro F001-${index + 1}`, direction: "in", kind: "receivable", currency: "USD", source_amount: "59.123456", amount: "59.123456", original_due_date: "2026-10-21", due_date: "2026-10-21", point_key: null, fixed_point: false, default_included: true, included: true, in_horizon: true, is_overdue: false, needs_review: false, note: "", fingerprint: `fingerprint-${index}` }));
  const days = Array.from({ length: 12 }, (_, index) => ({ date: `2026-10-${21 + index}`, opening: "2294.800000", incoming: index === 0 ? "3843.024640" : "0", outgoing: "0.000000", closing: "6137.824640", negative: false, requires_prior_receipts: false, source_keys: index === 0 ? items.map(item => item.key) : [] }));
  const forecast = { business_date: "2026-10-21", end_date: "2026-11-19", points: [], items, timelines: [{ key: "currency:USD", name: "Total interno · USD", currency: "USD", opening_balance: "2294.800000", closing_balance: "6137.824640", first_negative_date: null, days }], warnings: [], stale_source_keys: [], in_transit_by_currency: {}, method: "Criterios del cálculo", generated_at: "2026-10-21T10:00:00" };
  vi.mocked(apiClient.request).mockImplementation(async path => path === "/api/v1/cash-forecast/preview" ? forecast as never : [] as never);
}

it("mantiene filas compactas y abre los compromisos en un modal paginado", async () => {
  mockForecastDocuments();
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  render(<CashForecastPanel canWrite revision={0} />);
  const trigger = await screen.findByRole("button", { name: "Ver 65 compromisos del 2026-10-21" });
  const row = trigger.closest("tr")!;
  expect(row.querySelector("details")).toBeNull();
  expect(within(row).getByText("2,294.80")).toBeTruthy();
  expect(within(row).queryByText("2294.800000")).toBeNull();
  expect(within(screen.getByRole("tabpanel")).getByText("1–10 de 12 registros")).toBeTruthy();
  trigger.focus();
  fireEvent.click(trigger);
  const dialog = await screen.findByRole("dialog", { name: "Compromisos del 21/10/2026" });
  expect(within(dialog).getByText("Cobro F001-1")).toBeTruthy();
  expect(within(dialog).queryByText("Cobro F001-11")).toBeNull();
  fireEvent.click(within(dialog).getByRole("button", { name: "Página siguiente" }));
  expect(within(dialog).getByText("Cobro F001-11")).toBeTruthy();
  fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar compromisos" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(trigger);
});

it("separa documentos en una pestaña y conserva la precisión de sus hipótesis al calcular", async () => {
  mockForecastDocuments();
  render(<CashForecastPanel canWrite revision={0} />);
  await screen.findByRole("button", { name: "Ver 65 compromisos del 2026-10-21" });
  fireEvent.click(screen.getByRole("tab", { name: "Documentos e hipótesis" }));
  const panel = screen.getByRole("tabpanel");
  expect(within(panel).getByText("1–10 de 65 registros")).toBeTruthy();
  const source = within(panel).getByText("Cobro F001-1").closest("details")!;
  expect(source.open).toBe(false);
  fireEvent.click(source.querySelector("summary")!);
  const amountInput = within(source).getByRole("spinbutton", { name: "Importe de la hipótesis" }) as HTMLInputElement;
  expect(amountInput.value).toBe("59.123456");
  fireEvent.change(amountInput, { target: { value: "50.123456" } });
  fireEvent.click(screen.getByRole("button", { name: "Calcular con datos actuales" }));
  await waitFor(() => expect(vi.mocked(apiClient.request).mock.calls.some(([path, options]) => path === "/api/v1/cash-forecast/preview" && JSON.parse(String(options?.body)).overrides.some((entry: { amount: string }) => entry.amount === "50.123456"))).toBe(true));
  fireEvent.click(screen.getByRole("tab", { name: "Operaciones manuales" }));
  expect(screen.getByRole("button", { name: "Añadir operación prevista" })).toBeTruthy();
});
