import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { CashDenominationCounter } from "../src/features/caja/components/CashDenominationCounter";
import { InventoryTransferDialog } from "../src/features/inventario/components/InventoryTransferDialog";
import { PhysicalCountDialog } from "../src/features/inventario/components/PhysicalCountDialog";
import { CustomRoleDialog } from "../src/features/seguridad/components/CustomRoleDialog";
import { ReportScheduleBuilder, ReportScheduleConfig } from "../src/features/reportes/components/ReportScheduleBuilder";

const toast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockResolvedValue({});
  vi.spyOn(window, "confirm").mockReturnValue(true);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Recorridos de continuación", () => {
  it("suma denominaciones sin mezclar tarjetas con efectivo", () => {
    render(<CashDenominationCounter currency="PEN" />);
    fireEvent.change(screen.getByRole("spinbutton", { name: "Cantidad de S/ 100.00" }), { target: { value: "2" } });
    fireEvent.change(screen.getByRole("spinbutton", { name: "Total de tarjetas" }), { target: { value: "50" } });
    expect((document.querySelector('[name="counted_cash"]') as HTMLInputElement).value).toBe("200.00");
    expect(JSON.parse((document.querySelector('[name="non_cash_json"]') as HTMLInputElement).value)).toEqual({ CARD: "50" });
  });

  it("recibe dos productos y conserva la recepción parcial por artículo", async () => {
    const saved = vi.fn();
    render(<InventoryTransferDialog transfer={{ id: "trf", document_number: "TRF-01", source_warehouse_id: "a", destination_warehouse_id: "b", status: "in_transit", created_at: "2026-10-14", lines: [{ product_id: "p1", quantity: "5", processed_quantity: "2", damaged_quantity: "0", unit_cost: "10" }, { product_id: "p2", quantity: "4", processed_quantity: "0", damaged_quantity: "0", unit_cost: "5" }] }} products={[{ id: "p1", name: "Tablero", sku: "TAB-01" }, { id: "p2", name: "Listón", sku: "LIS-01" }]} warehouses={[]} onClose={vi.fn()} onSaved={saved} />);
    const received = screen.getAllByLabelText("Cantidad conforme");
    fireEvent.change(received[0], { target: { value: "2" } });
    fireEvent.change(received[1], { target: { value: "3" } });
    fireEvent.change(screen.getAllByLabelText("Cantidad dañada")[1], { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar recepción" }));
    await waitFor(() => expect(saved).toHaveBeenCalled());
    const options = vi.mocked(apiClient.request).mock.calls[0][1];
    expect(JSON.parse(String(options?.body)).items).toEqual([{ product_id: "p1", quantity_received: "2", quantity_damaged: "0" }, { product_id: "p2", quantity_received: "3", quantity_damaged: "1" }]);
  });

  it("bloquea el envío de un conteo hasta registrar explícitamente los ceros", async () => {
    render(<PhysicalCountDialog count={{ id: "cnt", count_code: "CNT-01", version: 3, warehouse_id: "a", status: "in_progress", notes: null, cutoff_at: "2026-10-14", created_at: "2026-10-14", lines: [{ id: "l", product_id: "p", counted_quantity: "0", snapshot_system_quantity: null, discrepancy_quantity: null }] }} products={[{ id: "p", sku: "TAB-01", name: "Tablero" }]} onClose={vi.fn()} onSaved={vi.fn()} />);
    expect((screen.getByRole("button", { name: "Enviar a revisión" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Cantidad contada de TAB-01"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar a revisión" }));
    await waitFor(() => expect(apiClient.request).toHaveBeenCalledWith("/api/v1/inventory/counts/cnt/entries", expect.objectContaining({ body: JSON.stringify({ items: [{ product_id: "p", quantity: "0" }], submit: true, version: 3 }) })));
  });

  it("muestra usuarios afectados antes de editar un rol", async () => {
    vi.mocked(apiClient.request).mockResolvedValue({ affected_users: 1, users: [{ name: "Ana", email: "ana@example.com", is_active: true }] });
    const role = { role: "custom", title: "Supervisor", permissions: ["sales:read"] };
    render(<CustomRoleDialog role={role} roles={[role]} availablePermissions={["sales:read"]} onClose={vi.fn()} onSaved={vi.fn()} />);
    await screen.findByText("1 usuarios afectados");
    expect(screen.getByText(/ana@example.com/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Nombre visible"), { target: { value: "Supervisor comercial" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    fireEvent.click(await screen.findByRole("button", { name: "Actualizar" }));
    await waitFor(() => expect(apiClient.request).toHaveBeenCalledWith("/api/v1/roles/custom", expect.objectContaining({ method: "PATCH", body: expect.stringContaining('"affected_users":1') })));
  });

  it("permite elegir frecuencia sin escribir cron", () => {
    const value: ReportScheduleConfig = { frequency: "daily", hour: 8, minute: 0, weekday: 1, day: 1, start_date: "2026-10-14" };
    const changed = vi.fn();
    render(<ReportScheduleBuilder value={value} onChange={changed} />);
    fireEvent.change(screen.getByLabelText("Hora local"), { target: { value: "15:45" } });
    expect(changed).toHaveBeenCalledWith(expect.objectContaining({ hour: 15, minute: 45 }));
    expect(screen.queryByText(/expresión cron/i)).toBeNull();
  });
});
