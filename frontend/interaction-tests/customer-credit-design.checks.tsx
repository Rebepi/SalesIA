import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CustomerCreditPanel } from "../src/features/devoluciones/components/CustomerCreditPanel";
import { apiClient } from "../src/api/client";

vi.mock("../src/ui/components/RemoteEntitySelect", () => ({ RemoteEntitySelect: ({ label, onChange }: { label: string; onChange: (value: string, option: { data: { id: string; legal_name: string } }) => void }) => <button onClick={() => onChange("c1", { data: { id: "c1", legal_name: "Cliente" } })}>{label}</button> }));
vi.mock("../src/features/devoluciones/components/CustomerCreditConversions", () => ({ CustomerCreditConversions: () => <details><summary>Conversiones</summary></details> }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const book = { balances: [], can_apply: true, warnings: [], sources: [], reservations: [], movements: [], allocations: [], unapplied_payments: [], unapplied_balances: [] };

it("separa controles y tabla, muestra el vacío y permite actualizar el libro", async () => {
  vi.spyOn(apiClient, "getMe").mockResolvedValue({ permissions: [] } as never);
  const request = vi.spyOn(apiClient, "request").mockResolvedValue(book as never);
  const { container } = render(<CustomerCreditPanel standalone canWrite={false} revision={0} onChanged={vi.fn()} />);
  expect(screen.getByText("Selecciona un cliente")).toBeTruthy();
  expect((screen.getByRole("button", { name: "Actualizar libro" }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Cliente" }));
  await screen.findByText("Sin créditos para esta selección");
  expect(container.querySelector(".credit-controls")).toBeTruthy();
  expect(container.querySelector(".credit-sources-card")).toBeTruthy();
  expect(screen.queryByText("Selecciona un cliente")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Actualizar libro" }));
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
});

it("presenta importes por moneda y conserva el filtro y los créditos seleccionables", async () => {
  vi.spyOn(apiClient, "getMe").mockResolvedValue({ permissions: [] } as never);
  const request = vi.spyOn(apiClient, "request").mockResolvedValue({ ...book, balances: [{ currency: "USD", available_balance: "1250.123456", reserved_balance: "20", expired_balance: "0", ledger_balance: "1270.123456" }], sources: [{ id: "credit-1", currency: "USD", original_amount: "1270.123456", remaining_amount: "1270.123456", available_amount: "1250.123456", reserved_amount: "20", reference_type: "return", reference_id: "return-1", expired: false, expires_at: null }] } as never);
  render(<CustomerCreditPanel standalone canWrite={false} revision={0} onChanged={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Cliente" }));
  await screen.findByText("USD 1,250.12");
  fireEvent.click(screen.getByRole("combobox", { name: "Moneda" }));
  fireEvent.click(screen.getByRole("option", { name: "USD" }));
  await waitFor(() => expect(request.mock.calls.some(([path]) => path === "/api/v1/customers/c1/store-credit?currency=USD")).toBe(true));
  expect(screen.getByRole("checkbox", { name: "Elegir crédito credit-1" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Aplicar saldo a la venta" })).toBeNull();
});
