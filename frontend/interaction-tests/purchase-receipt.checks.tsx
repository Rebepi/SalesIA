import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { PurchasesWorkspaceTab } from "../src/features/compras/components/PurchasesWorkspaceTab";
import { PurchaseReceiptDialog } from "../src/features/compras/components/PurchaseReceiptDialog";
import { InventoryTraceDialog } from "../src/features/inventario/components/InventoryTraceDialog";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));
const context = { order_id: "order", version: 4, status: "partially_received", warehouse_id: "warehouse", warehouse_name: "Central", supplier_name: "Proveedor real", currency: "PEN", locations: [], receipts: [], lines: [{ product_id: "lot", name: "Barniz", sku: "BAR-01", tracking_mode: "LOT", ordered_quantity: "5", received_quantity: "1", rejected_quantity: "0", pending_quantity: "4", unit_cost: "9" }, { product_id: "serial", name: "Equipo", sku: "EQU-01", tracking_mode: "SERIAL", ordered_quantity: "2", received_quantity: "0", rejected_quantity: "0", pending_quantity: "2", unit_cost: "25" }] };

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(async path => path.includes("receiving-context") ? context : { id: "receipt" });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function quality(sku: string, value: string) {
  fireEvent.change(document.querySelector(`select[aria-label="Inspección de ${sku}"]`)!, { target: { value } });
}

describe("Recepción vinculada y trazabilidad", () => {
  it("exige elegir la recepción real antes de aplicar costos a una orden", async () => {
    vi.mocked(apiClient.request).mockImplementation(async path => path.includes("receiving-context") ? { receipts: [{ id: "actual-receipt", status: "accepted", created_at: "2026-10-14T15:00:00Z", returnable_lines: [{ product_id: "p1", name: "Barniz", sku: "BAR-01", quantity: "2", returnable_quantity: "2", unit_cost: "9", lots: [], serial_numbers: [] }] }] } : { items: [], count: 0 });
    render(<PurchasesWorkspaceTab canWrite initialModalType="landed_cost" initialActiveOrder={{ id: "order", document_number: "OC-1", supplier_id: "supplier", warehouse_id: "warehouse", status: "received", version: 2, lines: [], created_at: "2026-10-14", details: { currency: "PEN" } }} />);
    expect((screen.getByRole("button", { name: "Aplicar Costos" }) as HTMLButtonElement).disabled).toBe(true);
    await waitFor(() => expect(document.querySelector('select[aria-label="Recepción de origen"] option[value="actual-receipt"]')).toBeTruthy());
    fireEvent.click(screen.getByRole("combobox", { name: "Recepción de origen" }));
    fireEvent.click(await screen.findByRole("option", { name: /BAR-01: 2/ }));
    fireEvent.change(screen.getByPlaceholderText("150.00"), { target: { value: "6" } });
    fireEvent.submit(screen.getByPlaceholderText("150.00").closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Aplicar costos", exact: true }));
    await waitFor(() => expect(apiClient.request).toHaveBeenCalledWith("/api/v1/goods-receipts/actual-receipt/landed-cost", expect.objectContaining({ method: "POST", headers: expect.objectContaining({ "Idempotency-Key": expect.any(String) }) })));
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path.includes("/goods-receipts/order/"))).toBe(false);
  });

  it("recibe dos productos con lote y series retenidas sin volver a escribir almacén ni costo", async () => {
    const saved = vi.fn();
    render(<PurchaseReceiptDialog orderId="order" onClose={vi.fn()} onSaved={saved} />);
    await screen.findByText("Barniz");
    fireEvent.change(screen.getByLabelText("Cantidad recibida de BAR-01"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Agregar lote de BAR-01" }));
    fireEvent.change(screen.getByLabelText("Código de lote 1 de BAR-01"), { target: { value: "L-01" } });
    fireEvent.input(screen.getByLabelText("Caducidad 1 de BAR-01"), { target: { value: "2099-01-01" } });
    fireEvent.change(screen.getByLabelText("Series de EQU-01"), { target: { value: "SER-1\nSER-2" } });
    quality("EQU-01", "quarantine");
    fireEvent.change(screen.getByLabelText("Observaciones de EQU-01"), { target: { value: "Inspección técnica pendiente" } });
    fireEvent.submit(screen.getByLabelText("Cantidad recibida de BAR-01").closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Registrar recepción" }));
    await waitFor(() => expect(saved).toHaveBeenCalledWith("receipt"));
    const request = vi.mocked(apiClient.request).mock.calls.find(([path]) => path === "/api/v1/goods-receipts");
    const body = JSON.parse(String(request?.[1]?.body));
    expect(body.order_version).toBe(4);
    expect(body.warehouse_id).toBe("warehouse");
    expect(body.items).toHaveLength(2);
    expect(body.items[0]).toMatchObject({ product_id: "lot", quantity: "2", unit_cost: "9", lots: [{ lot_code: "L-01", quantity: "2", manufacture_date: null, expiration_date: "2099-01-01" }] });
    expect(body.items[1]).toMatchObject({ product_id: "serial", quantity: "2", unit_cost: "25", inspection_status: "quarantine", serial_numbers: ["SER-1", "SER-2"] });
  });

  it("rechaza cantidades de lote incompletas sin enviar una recepción", async () => {
    render(<PurchaseReceiptDialog orderId="order" onClose={vi.fn()} onSaved={vi.fn()} />);
    const quantity = await screen.findByLabelText("Cantidad recibida de BAR-01");
    fireEvent.change(quantity, { target: { value: "2" } });
    fireEvent.submit(quantity.closest("form")!);
    expect(await screen.findByText("Los lotes de BAR-01 deben sumar la cantidad recibida.")).toBeTruthy();
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path === "/api/v1/goods-receipts")).toBe(false);
  });

  it("conserva la recepción parcial al actualizar una versión en conflicto", async () => {
    let version = 4;
    vi.mocked(apiClient.request).mockImplementation(async path => {
      if (path.includes("receiving-context")) return { ...context, version };
      if (version === 4) { version = 5; throw { detail: "La orden cambió. Actualiza los saldos antes de recibir." }; }
      return { id: "receipt" };
    });
    const saved = vi.fn();
    render(<PurchaseReceiptDialog orderId="order" onClose={vi.fn()} onSaved={saved} />);
    const serials = await screen.findByLabelText("Series de EQU-01");
    fireEvent.change(serials, { target: { value: "SER-1" } });
    fireEvent.submit(serials.closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Registrar recepción" }));
    await screen.findByText("La orden cambió. Actualiza los saldos antes de recibir.");
    fireEvent.click(screen.getByRole("button", { name: "Actualizar saldos" }));
    await screen.findByText(/versión 5/);
    expect((screen.getByLabelText("Cantidad recibida de EQU-01") as HTMLInputElement).value).toBe("1");
    fireEvent.submit(screen.getByLabelText("Series de EQU-01").closest("form")!);
    fireEvent.click(await screen.findByRole("button", { name: "Registrar recepción" }));
    await waitFor(() => expect(saved).toHaveBeenCalledWith("receipt"));
  });

  it("mantiene la recepción en lectura para un usuario sin permiso de escritura", async () => {
    render(<PurchaseReceiptDialog orderId="order" canWrite={false} onClose={vi.fn()} onSaved={vi.fn()} />);
    await screen.findByLabelText("Cantidad recibida de BAR-01");
    expect((screen.getByRole("button", { name: "Confirmar Recepción" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.submit(screen.getByLabelText("Cantidad recibida de BAR-01").closest("form")!);
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path === "/api/v1/goods-receipts")).toBe(false);
  });

  it("muestra producto, almacén y eventos comprensibles en la trazabilidad", async () => {
    vi.mocked(apiClient.request).mockResolvedValue({ code: "SER-1", product_name: "Equipo", sku: "EQU-01", status: "IN_STOCK", warehouse: "Central", location: "A-1", coverage: "Recepciones con seguimiento", truncated: false, events: [{ id: "event", date: "2026-10-14T15:00:00Z", title: "Cuarentena liberada a stock", code: "CLASSIFY_PURCHASE_QUARANTINE", quantity: "1" }] });
    render(<InventoryTraceDialog id="serial" kind="serial" onClose={vi.fn()} />);
    expect(await screen.findByText("Equipo · EQU-01")).toBeTruthy();
    expect(screen.getByText("Almacén de registro: Central · Ubicación: A-1")).toBeTruthy();
    expect(screen.getByText("Cuarentena liberada a stock")).toBeTruthy();
  });
});
