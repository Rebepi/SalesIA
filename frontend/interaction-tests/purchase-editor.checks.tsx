import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { PurchaseOrderEditor, PurchaseEditorSource } from "../src/features/compras/components/PurchaseOrderEditor";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));
const source: PurchaseEditorSource = { id: "req1", version: 3, warehouse_id: "w1", supplier_id: "s1", lines: [{ product_id: "p1", quantity: "4", unit_cost: "10" }, { product_id: "p2", quantity: "2", unit_cost: "20" }] };
const warehouses = [{ warehouse_id: "w1", code: "ALM-01", name: "Principal" }];

beforeEach(() => {
  sessionStorage.clear();
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (path.includes("/products/")) return { id: path.split("/").pop(), name: path.endsWith("p1") ? "Tablero" : "Listón", sku: path.endsWith("p1") ? "TAB-01" : "LIS-01", unit_cost: "10" };
    if (path.endsWith("/suppliers/s1")) return { id: "s1", legal_name: "Proveedor seleccionado", tax_id: "20123456789", currency: "PEN", payment_terms_days: 45 };
    return { items: [] };
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Compras de varias líneas", () => {
  it("bloquea una conversión cuyo origen falla y recupera el borrador independiente", async () => {
    const props = { isOpen: true, mode: "order" as const, warehouses, companyCurrency: "PEN", defaultTaxRate: "0.18", onCreateSupplier: vi.fn(), onClose: vi.fn(), onSaved: vi.fn() };
    const view = render(<PurchaseOrderEditor {...props} source={source} />);
    await screen.findByLabelText("Cantidad de TAB-01");
    vi.mocked(apiClient.request).mockRejectedValue({ detail: "Origen no disponible" });
    view.rerender(<PurchaseOrderEditor {...props} source={{ ...source, id: "missing" }} />);
    await screen.findByText(/No se pudo cargar el origen/);
    expect((screen.getByRole("button", { name: "Crear Orden" }) as HTMLButtonElement).disabled).toBe(true);
    view.rerender(<PurchaseOrderEditor {...props} isOpen={false} />);
    view.rerender(<PurchaseOrderEditor {...props} />);
    expect(screen.queryByLabelText("Cantidad de TAB-01")).toBeNull();
    expect(screen.getByText("Agrega productos para preparar el documento.")).toBeTruthy();
  });

  it("conserva cantidades aprobadas y envía descuentos, impuestos y referencia de la requisición", async () => {
    const saved = vi.fn();
    render(<PurchaseOrderEditor isOpen mode="order" source={source} warehouses={warehouses} companyCurrency="PEN" defaultTaxRate="0.18" onCreateSupplier={vi.fn()} onClose={vi.fn()} onSaved={saved} />);
    const quantity = await screen.findByLabelText("Cantidad de TAB-01");
    expect((quantity as HTMLInputElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Quitar TAB-01" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Descuento de TAB-01"), { target: { value: "10" } });
    expect(screen.getByText(/Total S\/\s*89.68/)).toBeTruthy();
    fireEvent.submit(quantity.closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Crear documento" }));
    await waitFor(() => expect(saved).toHaveBeenCalled());
    const call = vi.mocked(apiClient.request).mock.calls.find(([path]) => path === "/api/v1/purchase-orders");
    const body = JSON.parse(String(call?.[1]?.body));
    expect(body.source_requisition_id).toBe("req1");
    expect(body.source_version).toBe(3);
    expect(body.currency).toBe("PEN");
    expect(body.payment_terms_days).toBe(45);
    expect(body.items).toEqual([{ product_id: "p1", quantity: "4", unit_cost: "10", discount_percentage: "10", tax_rate: "0.18" }, { product_id: "p2", quantity: "2", unit_cost: "20", discount_percentage: "0", tax_rate: "0.18" }]);
  });

  it("permite corregir cantidades sugeridas antes de crear una requisición", async () => {
    render(<PurchaseOrderEditor isOpen mode="requisition" source={{ ...source, id: undefined }} warehouses={warehouses} companyCurrency="PEN" defaultTaxRate="0.18" onCreateSupplier={vi.fn()} onClose={vi.fn()} onSaved={vi.fn()} />);
    const quantity = await screen.findByLabelText("Cantidad de TAB-01");
    expect((quantity as HTMLInputElement).disabled).toBe(false);
    fireEvent.change(quantity, { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Justificación"), { target: { value: "Demanda revisada manualmente" } });
    fireEvent.submit(quantity.closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Crear documento" }));
    await waitFor(() => expect(apiClient.request).toHaveBeenCalledWith("/api/v1/purchases/requisitions", expect.objectContaining({ method: "POST", body: expect.stringContaining('"quantity":"7"') })));
  });
});
