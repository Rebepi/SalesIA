import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { VentasDevolucionModal } from "../src/features/ventas/components/VentasDevolucionModal";
import { SaleReturnCompletion } from "../src/features/devoluciones/components/SaleReturnCompletion";
import type { SaleRecord } from "../src/features/ventas/types/ventas";
import type { SaleDetailData } from "../src/features/ventas/types/SaleDetailModal";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
const sale = { id: "s1", sale_id: "s1", number: "B001-00000007", customer_name: "Cliente", currency: "PEN", status: "paid", warehouse_id: "w1", branch_id: "b1", total_amount: "118", paid_amount: "118", lines: [{ id: "l1", product_id: "p1", name: "Teclado", product_name: "Teclado", sku: "TEC", quantity: "2", unit_price: "50" }], payments: [{ id: "pay1", currency: "PEN", amount: "118", payment_method: "CASH", created_at: "2026-10-21" }] } as unknown as SaleRecord & SaleDetailData;
const rule = { returnable: true, days: 30, allowed_conditions: ["unused"], allowed_packaging: ["sealed"], evidence_required: false, allow_exceptions: true, retention_percentage: "10", retention_description: "Revisión" };
const eligible = { currency: "PEN", business_date: "2026-10-21", can_authorize_exception: false, can_grant_store_credit: true, independent_review_required: false, lines: [{ sale_line_id: "l1", product_id: "p1", sku: "TEC", product_name: "Teclado", unit_price: "50", tax_rate_snapshot: "0.18", original_quantity: "2", returned_quantity: "1", eligible_quantity: "1", return_policy: { version: 1, source: "sale_snapshot", product_type: "goods", sold_on: "2026-10-15", rule }, policy_evaluation: { deadline: "2026-11-15", eligible: true, reasons: [] } }] };
const settlement = { currency: "PEN", available_amount: "53.10", can_settle: true, can_grant_store_credit: true, debt_to_offset: "0", valuation: { refundable_total: "53.10", retained_total: "5.90" }, movements: [], warnings: [] };
async function respond(path: string, options?: { method?: string }) {
  if (path === "/api/v1/sales/s1") return sale;
  if (path === "/api/v1/returns?sale_id=s1") return [];
  if (path.endsWith("/eligible")) return eligible;
  if (path === "/api/v1/returns" && options?.method === "POST") return { id: "r1", status: "requested" };
  if (path.endsWith("/accept")) return { id: "r1", status: "accepted", valuation: settlement.valuation, settlement };
  if (path === "/api/v1/return-settlements/r1") return settlement;
  if (path === "/api/v1/refund-options/pay1") return { payment_method: "CASH", currency: "PEN", available_amount: "118", returns: [{ id: "r1", available_amount: "53.10" }], cash_sessions: [{ id: "cash1", terminal_code: "Caja Lima", balance: "200" }] };
  if (path.startsWith("/api/v1/products/search-availability")) return { items: [{ id: "p2", name: "Mouse", sku: "MOU", unit_price: "20", tax_rate: "0.18", available_quantity: "5", track_inventory: true }] };
  if (path.endsWith("/exchange")) return { exchange_sale_id: "s2", new_sale_total: "23.60", return_credit_applied: "23.60", difference: "-29.50", remaining_return_value: "29.50" };
  return {};
}
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(async (path, options) => respond(path, options) as never);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const bodyFor = (path: string) => JSON.parse(String(vi.mocked(apiClient.request).mock.calls.find(([url, options]) => url === path && options?.method === "POST")?.[1]?.body));
async function proceed() { for (let step = 0; step < 3; step++) fireEvent.click(screen.getByRole("button", { name: "Siguiente" })); }

it("carga líneas elegibles desde Ventas y crea y acepta usando almacén, línea y destinos reales", async () => {
  const success = vi.fn();
  render(<VentasDevolucionModal isOpen sale={sale} onClose={vi.fn()} onSuccess={success} />);
  const quantity = await screen.findByRole("spinbutton", { name: "Cantidad a devolver de Teclado" });
  expect((quantity as HTMLInputElement).max).toBe("1");
  fireEvent.change(quantity, { target: { value: "10" } });
  expect((quantity as HTMLInputElement).value).toBe("1");
  await proceed();
  fireEvent.click(screen.getByRole("button", { name: "Confirmar devolución y efectos" }));
  await screen.findByText("Devolución confirmada con éxito");
  expect(bodyFor("/api/v1/returns")).toMatchObject({ warehouse_id: "w1", sale_id: "s1", items: [{ product_id: "p1", sale_line_id: "l1", quantity: "1", disposition: "RESTOCK", condition: "unused", packaging: "sealed" }] });
  expect(bodyFor("/api/v1/returns/r1/accept")).toMatchObject({ create_credit_note: true, credit_action: "CREDIT_NOTE" });
  expect(success).toHaveBeenCalledWith({ returnId: "r1" });
  expect(screen.queryByPlaceholderText("PIN de supervisor")).toBeNull();
  expect(apiClient.request).not.toHaveBeenCalledWith("/api/v1/cash-sessions?status=open");
});

it("registra una solicitud pendiente cuando se exige revisión independiente sin simular aceptación", async () => {
  vi.mocked(apiClient.request).mockImplementation(async (path, options) => path.endsWith("/eligible") ? { ...eligible, independent_review_required: true } as never : respond(path, options) as never);
  render(<VentasDevolucionModal isOpen sale={sale} onClose={vi.fn()} onSuccess={vi.fn()} />);
  await screen.findByText("Teclado"); await proceed();
  fireEvent.click(screen.getByRole("button", { name: "Enviar solicitud a revisión" }));
  await screen.findByText("Solicitud de devolución registrada");
  expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path.endsWith("/accept"))).toBe(false);
  expect(screen.queryByText("Devolución confirmada con éxito")).toBeNull();
});

it("reintenta la aceptación fallida sin duplicar la solicitud creada", async () => {
  let failures = 1;
  vi.mocked(apiClient.request).mockImplementation(async (path, options) => { if (path.endsWith("/accept") && failures-- > 0) throw { detail: "Fallo temporal" }; return respond(path, options) as never; });
  render(<VentasDevolucionModal isOpen sale={sale} onClose={vi.fn()} onSuccess={vi.fn()} />);
  await screen.findByText("Teclado"); await proceed();
  fireEvent.click(screen.getByRole("button", { name: "Confirmar devolución y efectos" }));
  await screen.findByText("Fallo temporal");
  fireEvent.click(screen.getByRole("button", { name: "Confirmar devolución y efectos" }));
  await screen.findByText("Devolución confirmada con éxito");
  expect(vi.mocked(apiClient.request).mock.calls.filter(([path]) => path === "/api/v1/returns")).toHaveLength(1);
  const attempts = vi.mocked(apiClient.request).mock.calls.filter(([path]) => path.endsWith("/accept"));
  expect(attempts[0][1]?.headers).toEqual(attempts[1][1]?.headers);
});

it("permite continuar una devolución pendiente desde otra sesión y liquidarla", async () => {
  vi.mocked(apiClient.request).mockImplementation(async (path, options) => path === "/api/v1/returns?sale_id=s1" ? [{ id: "r1", warehouse_id: "w1", status: "requested", reason: "Producto dañado", lines: [{ product_id: "p1", sale_line_id: "l1", quantity: "1", disposition: "QUARANTINE" }] }] as never : respond(path, options) as never);
  render(<VentasDevolucionModal isOpen sale={sale} onClose={vi.fn()} onSuccess={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Continuar devolución" }));
  fireEvent.click(screen.getByRole("button", { name: "Aceptar devolución revisada" }));
  await screen.findByText("Liquidación de la devolución");
  expect(bodyFor("/api/v1/returns/r1/accept").inspections[0].disposition).toBe("QUARANTINE");
});

it("registra el reembolso contra el pago real y la caja autorizada, bloqueando doble envío", async () => {
  const changed = vi.fn();
  render(<SaleReturnCompletion returnId="r1" sale={sale} warehouseId="w1" onChanged={changed} onBusyChange={vi.fn()} />);
  fireEvent.change(await screen.findByLabelText("Pago original"), { target: { value: "pay1" } });
  await screen.findByText(/Máximo reembolsable/);
  fireEvent.change(screen.getByLabelText("Referencia del desembolso"), { target: { value: "ACTA-001" } });
  const submit = screen.getByRole("button", { name: "Registrar desembolso" });
  fireEvent.click(submit); fireEvent.click(submit);
  await waitFor(() => expect(changed).toHaveBeenCalledOnce());
  expect(bodyFor("/api/v1/refunds")).toMatchObject({ payment_id: "pay1", return_id: "r1", cash_session_id: "cash1", amount: "53.1", payout_reference: "ACTA-001" });
  expect(vi.mocked(apiClient.request).mock.calls.filter(([path]) => path === "/api/v1/refunds")).toHaveLength(1);
});

it("crea una venta de cambio con productos elegidos y permite abrir su diferencia", async () => {
  const open = vi.fn();
  render(<SaleReturnCompletion returnId="r1" sale={sale} warehouseId="w1" onChanged={vi.fn()} onBusyChange={vi.fn()} onOpenSale={open} />);
  fireEvent.click(await screen.findByRole("button", { name: "Cambio de producto" }));
  fireEvent.click(await screen.findByRole("button", { name: "Agregar" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar cambio de producto" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ver venta de cambio y registrar diferencia" }));
  expect(open).toHaveBeenCalledWith("s2");
  expect(bodyFor("/api/v1/returns/r1/exchange")).toEqual({ warehouse_id: "w1", replacement_items: [{ product_id: "p2", quantity: "1" }] });
});
