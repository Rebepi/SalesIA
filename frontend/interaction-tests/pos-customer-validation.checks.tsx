import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { PosCustomerSelector } from "../src/features/ventas/components/PosCustomerSelector";
import { NewSalePOSModal } from "../src/features/ventas/components/NewSalePOSModal";
import { useNewSalePOSModal } from "../src/features/ventas/hooks/useNewSalePOSModal";
import { solicitarDatos } from "../src/features/ventas/api/NewSalePOSModal";
import { apiClient } from "../src/api/client";

vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() }) }));
vi.mock("../src/ui/components/ConfirmDialog", () => ({ useConfirm: () => ({ confirm: vi.fn(), ConfirmDialogNode: null }) }));
const walkIn = { id: "11111111-1111-4111-8111-111111111111", code: "CONSUMIDOR_FINAL", legal_name: "Consumidor final", doc_type: "SIN_DOCUMENTO", doc_number: "SIN_DOCUMENTO", is_walk_in: true };
const product = { id: "22222222-2222-4222-8222-222222222222", sku: "TEC", name: "Teclado prueba POS", unit_price: "50", tax_rate: "0.18", unit_of_measure: "NIU", available_quantity: "10", physical_quantity: "10", reserved_quantity: "0", track_inventory: true, has_lots: false, has_serials: false };
async function respond(path: string) {
  if (path.endsWith("/walk-in/ensure")) return walkIn;
  if (path.endsWith("/payment-methods")) return [];
  if (path.endsWith("/companies/current")) return { base_currency: "PEN" };
  if (path.endsWith("/settings")) return { default_tax_rate: "0.18", rounding_mode: "ROUND_HALF_EVEN" };
  if (path.startsWith("/api/v1/warehouses")) return [{ warehouse_id: "w1", code: "W001", name: "Almacén principal", branch_id: "b1" }];
  if (path.startsWith("/api/v1/branches")) return [{ branch_id: "b1", name: "Lima", timezone: "America/Lima" }];
  if (path.startsWith("/api/v1/products/search-availability")) return { items: [product], total_count: 1 };
  if (path.endsWith("/prices/preview")) return { product_id: product.id, final_unit_price: "50", subtotal: "50", tax_amount: "9", total_estimated: "59", discount_applied: "0", rules_applied: [] };
  return { items: [], total_count: 0 };
}
beforeEach(() => {
  localStorage.clear(); sessionStorage.clear();
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(async path => respond(path) as never);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("limita DNI a ocho dígitos y RUC a once, y reinicia el número al cambiar tipo", async () => {
  render(<PosCustomerSelector value={undefined} onChange={vi.fn()} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  fireEvent.click(screen.getByRole("button", { name: "Registrar cliente nuevo" }));
  const number = screen.getByRole("textbox", { name: "Número de documento" }) as HTMLInputElement;
  fireEvent.change(number, { target: { value: "abc123456789012" } });
  expect(number.value).toBe("12345678");
  expect(number.maxLength).toBe(8);
  fireEvent.click(screen.getByRole("combobox", { name: "Tipo de documento" }));
  fireEvent.click(screen.getByRole("option", { name: "RUC", exact: true }));
  expect(number.value).toBe("");
  fireEvent.change(number, { target: { value: "20-123456789999" } });
  expect(number.value).toBe("20123456789");
  expect(number.maxLength).toBe(11);
});

it("rechaza documentos incompletos antes de consultar o crear un cliente", async () => {
  render(<PosCustomerSelector value={undefined} onChange={vi.fn()} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  fireEvent.click(screen.getByRole("button", { name: "Registrar cliente nuevo" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Número de documento" }), { target: { value: "123" } });
  fireEvent.click(screen.getByRole("button", { name: "Validar" }));
  await screen.findByText("DNI debe contener exactamente 8 dígitos numéricos.");
  expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path.endsWith("/fiscal/validate"))).toBe(false);
  expect(vi.mocked(apiClient.request).mock.calls.some(([path, options]) => path === "/api/v1/customers" && options?.method === "POST")).toBe(false);
});

it("selecciona el consumidor final real en lugar de enviar un identificador de ejemplo", async () => {
  const change = vi.fn();
  render(<PosCustomerSelector value={undefined} onChange={change} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  fireEvent.click(screen.getByRole("button", { name: "Continuar como consumidor final" }));
  await waitFor(() => expect(change).toHaveBeenCalledWith(walkIn));
  expect(apiClient.request).toHaveBeenCalledWith("/api/v1/customers/walk-in/ensure", { method: "POST" });
});

it("recupera consumidores de borradores antiguos y nunca envía su identificador ficticio a precios", async () => {
  await solicitarDatos({ controller: new AbortController(), line: { product, quantity: 1 }, customer: { ...walkIn, id: "walk-in-default" }, couponCode: "" });
  const preview = vi.mocked(apiClient.request).mock.calls.find(([path]) => path.endsWith("/prices/preview"));
  expect(JSON.parse(String(preview?.[1]?.body)).customer_id).toBeNull();
  const { result } = renderHook(() => useNewSalePOSModal({ isOpen: true, onClose: vi.fn(), onSaleCreated: vi.fn() }));
  await waitFor(() => expect(result.current.customer?.id).toBe(walkIn.id));
  await act(async () => { await result.current.selectCustomer({ ...walkIn, id: "walk-in-default" }); });
  expect(result.current.customer?.id).toBe(walkIn.id);
});

it("un fallo de precios mantiene el catálogo y permite reintentar el cálculo", async () => {
  let failPrices = true;
  vi.mocked(apiClient.request).mockImplementation(async path => {
    if (path.endsWith("/prices/preview") && failPrices) throw { detail: "No se pudo verificar el precio" };
    return respond(path) as never;
  });
  render(<NewSalePOSModal isOpen onClose={vi.fn()} onSaleCreated={vi.fn()} />);
  const name = await screen.findByText(product.name);
  fireEvent.click(name.closest("button")!);
  await screen.findByText(/No se pudieron verificar los precios:/);
  expect(screen.queryByText("No pudimos cargar el catálogo")).toBeNull();
  expect(screen.getAllByText(product.name).length).toBeGreaterThan(0);
  const calls = vi.mocked(apiClient.request).mock.calls.filter(([path]) => path.endsWith("/prices/preview"));
  expect(JSON.parse(String(calls[0][1]?.body)).customer_id).toBe(walkIn.id);
  failPrices = false;
  fireEvent.click(screen.getByRole("button", { name: "Reintentar precios" }));
  await waitFor(() => expect(screen.queryByText(/No se pudieron verificar los precios:/)).toBeNull());
  expect(screen.queryByText("No pudimos cargar el catálogo")).toBeNull();
});
