import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { AccountsReceivableTab } from "../src/features/cuentas_cobrar/components/AccountsReceivableTab";
import { apiClient } from "../src/api/client";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ warning: vi.fn() }) }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });

function mockReceivables() {
  const base = { customer_id: "client", customer_name: "Cliente", total_amount: "100", paid_amount: "0", balance_due: "100", due_date: "2026-10-01", created_at: "2026-09-01", status: "confirmed", aging_bucket: "0-30" };
  vi.spyOn(apiClient, "request").mockResolvedValue({ items: [{ ...base, sale_id: "usd", series_number: "F001-USD", currency: "USD" }, { ...base, sale_id: "pen", series_number: "F001-PEN", currency: "PEN", aging_bucket: "not_due" }], totals_by_currency: { USD: { total_receivable: "100", total_disputed: "10", not_due: "0" }, PEN: { total_receivable: "100", total_disputed: "0", not_due: "100" } } } as never);
}

it("elimina el selector y conserva documentos y resúmenes separados por moneda", async () => {
  mockReceivables();
  render(<AccountsReceivableTab />);
  await screen.findByText("F001-USD");
  expect(screen.getByText("F001-PEN")).toBeTruthy();
  expect(screen.queryByLabelText("Moneda de la cartera")).toBeNull();
  const summary = screen.getByRole("region", { name: "Resumen de cuentas por cobrar" });
  const totalCard = within(summary).getByRole("heading", { name: "Total cartera pendiente" }).closest(".receivables-metric") as HTMLElement;
  expect(within(totalCard).getByText("USD 100.00")).toBeTruthy();
  expect(within(totalCard).getByText("PEN 100.00")).toBeTruthy();
  expect(within(totalCard).queryByText(/200.00/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Por vencer", exact: true }));
  expect(screen.queryByText("F001-USD")).toBeNull();
  expect(screen.getByText("F001-PEN")).toBeTruthy();
});

it("oculta las tarjetas desde configuración de vista, conserva la tabla y recuerda la preferencia", async () => {
  mockReceivables();
  const { unmount } = render(<AccountsReceivableTab />);
  await screen.findByText("F001-USD");
  fireEvent.click(screen.getByRole("button", { name: "Configurar vista · tarjetas activadas" }));
  fireEvent.click(screen.getByRole("switch", { name: /Mostrar tarjetas de información/ }));
  expect(screen.queryByRole("region", { name: "Resumen de cuentas por cobrar" })).toBeNull();
  expect(screen.getByText("F001-USD")).toBeTruthy();
  expect(localStorage.getItem("salesia_receivables_cards_visible")).toBe("false");
  fireEvent.keyDown(document, { key: "Escape" });
  expect(screen.queryByRole("group", { name: "Configuración de vista" })).toBeNull();
  unmount();
  render(<AccountsReceivableTab />);
  await screen.findByText("F001-USD");
  expect(screen.queryByRole("region", { name: "Resumen de cuentas por cobrar" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Configurar vista · tarjetas desactivadas" }));
  fireEvent.click(screen.getByRole("switch", { name: /Mostrar tarjetas de información/ }));
  expect(screen.getByRole("region", { name: "Resumen de cuentas por cobrar" })).toBeTruthy();
});
