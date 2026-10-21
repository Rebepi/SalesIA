import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { PosCustomerSelector } from "../src/features/ventas/components/PosCustomerSelector";
import { apiClient } from "../src/api/client";
const customer = (id: string) => ({ id, code: id, legal_name: `Cliente ${id}`, doc_type: "DNI", doc_number: "12345678", is_active: true });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });
it("ofrece cinco clientes del servidor al azar y permite crear sin buscar", async () => {
  vi.spyOn(apiClient, "getCompanyId").mockReturnValue("empresa");
  const change = vi.fn();
  const request = vi.spyOn(apiClient, "request").mockImplementation(async (path, options) => {
    if (path === "/api/v1/customers/duplicates/check") return { is_exact_duplicate: false, exact_matches: [] } as never;
    if (options?.method === "POST") return customer("nuevo") as never;
    return { items: Array.from({ length: 5 }, (_, index) => customer(String(index))) } as never;
  });
  render(<PosCustomerSelector value={undefined} onChange={change} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  await screen.findByText("Cliente 4");
  expect(screen.getByText("Clientes sugeridos al azar")).toBeTruthy();
  expect(request.mock.calls.some(([path]) => path === "/api/v1/customers?order=random&is_active=true&limit=5")).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Registrar cliente nuevo" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Nombre o razón social" }), { target: { value: "Cliente nuevo" } });
  fireEvent.change(screen.getByRole("textbox", { name: "Número de documento" }), { target: { value: "12345678" } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar y Usar" }));
  await waitFor(() => expect(change).toHaveBeenCalledWith(expect.objectContaining({ id: "nuevo" })));
  expect(JSON.parse(localStorage.getItem("salesia_pos_recent_customers_v1:empresa")!)).toEqual(["nuevo"]);
});
it("muestra recientes actualizados y evita la carga aleatoria cuando existen", async () => {
  vi.spyOn(apiClient, "getCompanyId").mockReturnValue("empresa");
  localStorage.setItem("salesia_pos_recent_customers_v1:empresa", JSON.stringify(["reciente"]));
  const request = vi.spyOn(apiClient, "request").mockResolvedValue(customer("reciente") as never);
  render(<PosCustomerSelector value={undefined} onChange={vi.fn()} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  await screen.findByText("Cliente reciente");
  expect(screen.getByText("Clientes recientes")).toBeTruthy();
  expect(request.mock.calls.some(([path]) => path === "/api/v1/customers/reciente")).toBe(true);
  expect(request.mock.calls.some(([path]) => String(path).includes("order=random"))).toBe(false);
});
it("busca con límite en el servidor", async () => {
  const request = vi.spyOn(apiClient, "request").mockResolvedValue({ items: [] } as never);
  render(<PosCustomerSelector value={undefined} onChange={vi.fn()} documentType="RECEIPT" />);
  fireEvent.click(screen.getByRole("button", { name: "Seleccionar cliente" }));
  fireEvent.change(screen.getByPlaceholderText("Buscar por nombre, RUC, DNI, teléfono o código..."), { target: { value: "Perez" } });
  await waitFor(() => expect(request.mock.calls.some(([path]) => path === "/api/v1/customers?search=Perez&is_active=true&limit=10")).toBe(true));
});
