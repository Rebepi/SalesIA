import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { ReturnSettlementPanel } from "../src/features/devoluciones/components/ReturnSettlementPanel";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("usa el paginador compartido y envía tamaño y desplazamiento al servidor", async () => {
  const request = vi.spyOn(apiClient, "request").mockResolvedValue({ items: [], total_count: 125 } as never);
  render(<ReturnSettlementPanel standalone canWrite={false} revision={0} onChanged={vi.fn()} />);
  await waitFor(() => expect((screen.getByRole("button", { name: "Página siguiente" }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole("combobox", { name: "Filas por página" }));
  fireEvent.click(screen.getByRole("option", { name: "25", exact: true }));
  await waitFor(() => expect(request.mock.calls.some(([path]) => String(path).includes("limit=25&offset=0"))).toBe(true));
  await waitFor(() => expect((screen.getByRole("button", { name: "Página siguiente" }) as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
  await waitFor(() => expect(request.mock.calls.some(([path]) => String(path).includes("limit=25&offset=25"))).toBe(true));
  expect(screen.getByRole("navigation", { name: "Paginación de la tabla" })).toBeTruthy();
});

it("abre la liquidación en un modal y permite cerrarlo sin perder la tabla", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  const detail = { return_id: "r1", document_number: "F001-123", currency: "USD", valuation: { refundable_total: "236.00", retained_total: "0" }, applied_amount: "0", remaining_financial_amount: "236.00", available_amount: "236.00", debt_to_offset: "0", can_grant_store_credit: true, can_settle: true, movements: [], warnings: [] };
  vi.spyOn(apiClient, "request").mockImplementation(async path => path === "/api/v1/return-settlements/r1" ? detail as never : { items: [detail], total_count: 1 } as never);
  render(<ReturnSettlementPanel standalone canWrite={false} revision={0} onChanged={vi.fn()} />);
  const trigger = await screen.findByRole("button", { name: "Ver liquidación" });
  trigger.focus();
  fireEvent.click(trigger);
  const dialog = await screen.findByRole("dialog", { name: "Liquidación de devolución" });
  expect(dialog.querySelector("form")).toBeNull();
  expect(dialog.textContent).toContain("236.00");
  fireEvent.click(screen.getByRole("button", { name: "Cerrar detalle" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(screen.getByRole("button", { name: "Ver liquidación" })).toBeTruthy();
  expect(document.activeElement).toBe(trigger);
  fireEvent.click(trigger);
  fireEvent(await screen.findByRole("dialog"), new Event("cancel", { bubbles: false, cancelable: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("mantiene la precisión de la aplicación y vincula el botón del pie al formulario", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  const detail = { return_id: "r2", currency: "USD", valuation: { refundable_total: "236.123456", retained_total: "0.000000" }, applied_amount: "0", remaining_financial_amount: "0", available_amount: "236.123456", debt_to_offset: "236.123456", can_grant_store_credit: true, can_settle: true, movements: [], warnings: [] };
  const changed = vi.fn();
  const request = vi.spyOn(apiClient, "request").mockImplementation(async path => String(path).includes("/r2") ? detail as never : { items: [detail], total_count: 1 } as never);
  render(<ReturnSettlementPanel standalone canWrite revision={0} onChanged={changed} />);
  fireEvent.click(await screen.findByRole("button", { name: "Ver liquidación" }));
  const dialog = await screen.findByRole("dialog", { name: "Liquidación de devolución" });
  expect(dialog.textContent).toContain("USD 236.12");
  const submit = screen.getByRole("button", { name: "Registrar aplicación" }) as HTMLButtonElement;
  expect(submit.form).toBe(dialog.querySelector("form"));
  fireEvent.change(screen.getByRole("textbox", { name: "Motivo y sustento" }), { target: { value: "Compensación documentada de la deuda" } });
  fireEvent.submit(submit.form!);
  await waitFor(() => expect(changed).toHaveBeenCalledOnce());
  const mutation = request.mock.calls.find(([path]) => path === "/api/v1/return-settlements/r2/settle-debt");
  expect(JSON.parse(String(mutation?.[1]?.body)).expected_available).toBe("236.123456");
});
