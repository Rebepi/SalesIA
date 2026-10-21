import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { CustomerCommercialCard } from "../src/features/clientes/ficha/CustomerCommercialCard";
import { ClientesPage } from "../src/features/clientes/pages/ClientesPage";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
const customer = { id: "c1", code: "CLI-1", legal_name: "Cliente Lima", doc_type: "RUC", doc_number: "20123456789", current_balance: "10.000000", is_active: true };
const cardProps = { customerId: "c1", customerName: customer.legal_name, canWrite: false, allCustomers: [], onClose: vi.fn(), onRefresh: vi.fn() };
const invoices = [
  { sale_id: "s1", series_number: "F001-1", currency: "PEN", status: "confirmed", total_amount: "100", paid_amount: "50", pending_balance: "50", created_at: "2026-10-01T10:00:00Z" },
  { sale_id: "s2", series_number: "F001-2", currency: "USD", status: "paid", total_amount: "20", paid_amount: "20", pending_balance: "0", created_at: "2026-10-02T10:00:00Z" },
  { sale_id: "s3", series_number: "F001-3", currency: "PEN", status: "cancelled", total_amount: "900", paid_amount: "0", pending_balance: "900", created_at: "2026-10-03T10:00:00Z" }
];
async function response(path: string) {
  if (path.endsWith("/quality")) return { score_percentage: 80, alerts: [] };
  if (path.endsWith("/statement")) return { invoices };
  if (path.endsWith("/segments")) return { matched_segments: [] };
  if (path.endsWith("/history")) return { timeline: [] };
  if (path.endsWith("/current")) return { base_currency: "PEN" };
  if (path.endsWith("/contacts") || path.endsWith("/addresses") || path.endsWith("/notes")) return [];
  if (path.endsWith("/commercial-terms")) return {};
  if (path === "/api/v1/sales/s1") return { id: "s1", customer_id: "c1", status: "confirmed", number: "F001-1", currency: "PEN", total_amount: "100", paid_amount: "50", lines: [{ product_id: "p1", product_name: "Teclado", sku: "TEC-1", quantity: "2", unit_price: "50", total_amount: "100" }], payments: [{ id: "pay1", payment_method: "cash", reference_code: "REC-1", amount: "50", created_at: "2026-10-01T10:00:00Z" }] };
  return customer;
}
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(async path => response(path) as never);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("mantiene cabecera y filas dentro de la misma tabla con saldo alineado", () => {
  render(<ClientesPage rows={[customer]} total={1} loading={false} search="" page={0} pageSize={50} error="" editorOpen={false} confirmationOpen={false} canWrite setSearch={vi.fn()} setPage={vi.fn()} setPageSize={vi.fn()} onRefresh={vi.fn()} openEntity={vi.fn()} setSelectedCustomer={vi.fn()} setConfirm={vi.fn()} />);
  const table = screen.getByRole("table", { name: "Clientes" });
  expect(table.querySelector("thead")).toBeTruthy();
  expect(table.querySelector("tbody")).toBeTruthy();
  expect(screen.getByRole("columnheader", { name: "Saldo" }).className).toContain("text-right");
  expect(screen.getByText("10.00").className).toContain("text-right");
});

it("abre un modal nativo, conserva importes por moneda y muestra productos y pagos reales", async () => {
  const close = vi.fn();
  render(<CustomerCommercialCard {...cardProps} onClose={close} />);
  const dialog = await screen.findByRole("dialog", { name: customer.legal_name });
  expect(dialog.className).toContain("customer-card-modal");
  fireEvent.click(await screen.findByRole("button", { name: "Ver compras y pagos" }));
  const summary = screen.getByText("Resumen de compras").parentElement!;
  expect(within(summary).getByText("PEN 100.00")).toBeTruthy();
  expect(within(summary).getAllByText("USD 20.00").length).toBe(2);
  expect(within(summary).queryByText("PEN 1,000.00")).toBeNull();
  fireEvent.change(screen.getByRole("textbox", { name: "Buscar compra" }), { target: { value: "F001-1" } });
  fireEvent.click(screen.getByRole("button", { name: "Ver compra" }));
  await screen.findByText("Teclado");
  expect(screen.getByText("TEC-1")).toBeTruthy();
  expect(screen.getByText("REC-1")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Repetir venta" })).toBeNull();
  expect(apiClient.request).toHaveBeenCalledWith("/api/v1/sales/s1", expect.objectContaining({ signal: expect.any(AbortSignal) }));
  fireEvent.click(screen.getByRole("button", { name: "Cerrar ficha" }));
  expect(close).toHaveBeenCalledOnce();
  fireEvent(dialog, new Event("cancel", { cancelable: true }));
  expect(close).toHaveBeenCalledTimes(2);
});

it("permite reintentar un detalle que falla y conserva el historial", async () => {
  let failures = 1;
  vi.mocked(apiClient.request).mockImplementation(async path => {
    if (path === "/api/v1/sales/s1" && failures-- > 0) throw new Error("Forbidden");
    return response(path) as never;
  });
  render(<CustomerCommercialCard {...cardProps} />);
  fireEvent.click(await screen.findByRole("button", { name: "Ver compras y pagos" }));
  fireEvent.click(screen.getAllByRole("button", { name: "Ver compra" })[0]);
  await screen.findByRole("alert");
  fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
  await screen.findByText("Teclado");
  expect(screen.getByText("F001-2")).toBeTruthy();
});

it("pagina el historial y conserva los importes restringidos sin convertirlos en ceros", async () => {
  vi.mocked(apiClient.request).mockImplementation(async path => {
    if (path.endsWith("/statement")) return { invoices: Array.from({ length: 12 }, (_, index) => ({ ...invoices[0], sale_id: `s${index}`, series_number: `F001-${index + 1}`, total_amount: null, paid_amount: null, pending_balance: null })) } as never;
    return response(path) as never;
  });
  render(<CustomerCommercialCard {...cardProps} />);
  fireEvent.click(await screen.findByRole("button", { name: "Ver compras y pagos" }));
  expect(screen.getAllByRole("button", { name: "Ver compra" })).toHaveLength(10);
  expect(screen.getAllByText("Restringido").length).toBeGreaterThan(0);
  expect(screen.queryByText("PEN 0.00")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
  expect(screen.getAllByRole("button", { name: "Ver compra" })).toHaveLength(2);
  expect(screen.getByText("F001-12")).toBeTruthy();
  fireEvent.change(screen.getByRole("textbox", { name: "Buscar compra" }), { target: { value: "F001-1" } });
  expect(screen.getByText(/Página 1 de 1/)).toBeTruthy();
});
