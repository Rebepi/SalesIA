import React, { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { NewSalePOSModal } from "../src/features/ventas/components/NewSalePOSModal";
import { CustomerEditorDrawer } from "../src/features/clientes/editor/CustomerEditorDrawer";
import { RemoteEntitySelect } from "../src/ui/components/RemoteEntitySelect";
import { ModalSurface } from "../src/ui/components/ModalSurface";
import { notifyEntityChanged } from "../src/ui/entityEvents";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));
const customer = { id: "c1", code: "CLI-01", legal_name: "Cliente existente", doc_type: "RUC", doc_number: "20123456789", credit_limit: "1000" };
const newCustomer = { ...customer, id: "c2", code: "CLI-02", legal_name: "Cliente nuevo", doc_number: "20234567890" };
const product = { id: "p1", sku: "TAB-01", name: "Tablero", unit_price: "10", available_quantity: "20", unit_of_measure: "NIU", track_inventory: true };

async function respond(path: string, options?: { method?: string }) {
  if (path.endsWith("/companies/current")) return { base_currency: "PEN" };
  if (path.endsWith("/settings")) return { default_tax_rate: "0.18", rounding_mode: "ROUND_HALF_EVEN", tax_included_in_price: false };
  if (path.includes("/warehouses")) return [{ warehouse_id: "w1", branch_id: "b1", code: "ALM-01", name: "Principal" }];
  if (path.includes("/branches")) return [{ branch_id: "b1", name: "Lima", timezone: "America/Lima" }];
  if (path.endsWith("walk-in/ensure") || path.endsWith("/customers/c1")) return customer;
  if (path.endsWith("/customers/c2")) return newCustomer;
  if (path.includes("duplicates/check")) return { exact_matches: [], potential_matches: [] };
  if (path.includes("fiscal/validate")) return { valid: true };
  if (path.endsWith("/customers") && options?.method === "POST") return newCustomer;
  if (path.includes("/customers")) return { items: [customer], total_count: 1 };
  if (path.includes("payment-methods")) return [];
  if (path.includes("cash-sessions")) return { session: null };
  if (path.includes("search-availability")) return { items: [product], total_count: 1 };
  if (path.includes("prices/preview")) return { product_id: "p1", final_unit_price: "10", total_estimated: "11.8", rules_applied: [] };
  return { items: [] };
}

beforeEach(() => {
  sessionStorage.clear();
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) { this.setAttribute("open", ""); });
  HTMLDialogElement.prototype.close = vi.fn(function (this: HTMLDialogElement) { this.removeAttribute("open"); });
  vi.spyOn(apiClient, "request").mockImplementation(respond as typeof apiClient.request);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Modales anidados y selectores", () => {
  it("no sustituye un producto faltante al repetir una venta", async () => {
    vi.mocked(apiClient.request).mockImplementation(async (path, options) => path === "/api/v1/sales/previous" ? { customer_id: "c1", warehouse_id: "w1", document_type: "RECEIPT", is_credit: false, status: "confirmed", version: 1, lines: [{ product_id: "missing", sku: "ORIGINAL", quantity: "1" }] } as never : respond(path, options) as never);
    render(<NewSalePOSModal isOpen sourceSaleId="previous" onClose={vi.fn()} onSaleCreated={vi.fn()} />);
    await screen.findByText("El producto ORIGINAL ya no está disponible. Revisa la venta de origen antes de repetirla.");
    expect(screen.queryByRole("button", { name: "Quitar Tablero" })).toBeNull();
  });

  it("abre el cliente como segundo diálogo nativo y conserva el producto al guardarlo", async () => {
    render(<NewSalePOSModal isOpen onClose={vi.fn()} onSaleCreated={vi.fn()} />);
    await screen.findByText("RUC 20123456789");
    fireEvent.change(screen.getByPlaceholderText("Escanear código o buscar por SKU o nombre"), { target: { value: "Tablero" } });
    fireEvent.click(await screen.findByRole("button", { name: /Tablero.*TAB-01/ }));
    const sale = screen.getByRole("dialog", { name: "Nueva Venta (Punto de Venta / Mostrador)" });
    fireEvent.click(within(sale).getByRole("combobox", { name: "Cliente" }));
    fireEvent.click(await screen.findByRole("button", { name: "Crear cliente rápido" }));
    const editor = screen.getByRole("dialog", { name: "Alta rápida de cliente" });
    expect(editor.tagName).toBe("DIALOG");
    expect(editor.hasAttribute("open")).toBe(true);
    expect(sale.hasAttribute("open")).toBe(true);
    fireEvent.change(within(editor).getByLabelText(/Número de Documento/), { target: { value: newCustomer.doc_number } });
    fireEvent.change(within(editor).getByLabelText("Razón Social / Nombre Completo"), { target: { value: newCustomer.legal_name } });
    await waitFor(() => expect((within(editor).getByRole("button", { name: "Guardar cliente" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.submit(within(editor).getByLabelText("Razón Social / Nombre Completo").closest("form")!);
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Alta rápida de cliente" })).toBeNull());
    expect(within(sale).getByRole("combobox", { name: "Cliente" }).textContent).toContain("Cliente nuevo");
    expect(within(sale).getByRole("button", { name: "Quitar Tablero" })).toBeTruthy();
  });

  it("cierra solo el editor con Escape y restaura el foco a la operación de origen", async () => {
    function Flow() {
      const [open, setOpen] = useState(false);
      return <ModalSurface labelledBy="source" onClose={vi.fn()}><h2 id="source">Operación</h2><button onClick={() => setOpen(true)}>Nuevo cliente</button><CustomerEditorDrawer isOpen={open} quickMode onClose={() => setOpen(false)} onSaved={vi.fn()} /></ModalSurface>;
    }
    render(<Flow />);
    const trigger = screen.getByRole("button", { name: "Nuevo cliente" });
    trigger.focus();
    fireEvent.click(trigger);
    fireEvent(screen.getByRole("dialog", { name: "Alta rápida de cliente" }), new Event("cancel", { cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Alta rápida de cliente" })).toBeNull());
    expect(document.activeElement).toBe(trigger);
    expect(screen.getByRole("dialog", { name: "Operación" }).hasAttribute("open")).toBe(true);
  });

  it("permite seleccionar con flechas y no cambia por un cliente creado en otro flujo", async () => {
    const changed = vi.fn();
    render(<RemoteEntitySelect value="" onChange={changed} endpoint="/api/v1/customers" entityType="customer" label="Cliente" mapOption={item => ({ value: String(item.id), label: String(item.legal_name), data: item })} />);
    act(() => notifyEntityChanged("customer", newCustomer));
    expect(changed).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("combobox", { name: "Cliente" }));
    await screen.findByRole("option", { name: "Cliente existente" });
    const search = screen.getByRole("combobox", { name: "Buscar Cliente" });
    fireEvent.keyDown(search, { key: "ArrowDown" });
    fireEvent.keyDown(search, { key: "Enter" });
    expect(changed).toHaveBeenCalledWith("c1", expect.objectContaining({ label: "Cliente existente" }));
  });
});
