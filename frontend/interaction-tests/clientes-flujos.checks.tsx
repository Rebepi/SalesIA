import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { OperationsWorkspace } from "../src/app/OperationsWorkspace";
import { CustomerEditorDrawer } from "../src/features/clientes/editor/CustomerEditorDrawer";
import { CustomerCommercialCard } from "../src/features/clientes/ficha/CustomerCommercialCard";
import { useListadoClientes } from "../src/features/clientes/hooks/useListadoClientes";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));
const customer = { id: "c1", code: "CLI-01", legal_name: "Comercial Lima", doc_type: "RUC", doc_number: "20123456789", email: "cliente@example.com", credit_limit: "5000", current_balance: "0", is_active: true };

async function respond(path: string, options?: { method?: string }) {
  if (path.endsWith("/companies/current")) return { company_id: "company", trade_name: "Empresa", base_currency: "PEN" };
  if (path.endsWith("/branches")) return [];
  if (path.endsWith("/quality")) return { score_percentage: 100, missing_fields: [], alerts: [], blocking_purchases: false };
  if (path.endsWith("/contacts")) return options?.method === "POST" ? {} : [{ id: "contact1", name: "Ana", role: "Compras", email: "ana@example.com", is_primary: true }];
  if (path.endsWith("/addresses") || path.endsWith("/notes")) return [];
  if (path.endsWith("/commercial-terms")) return { payment_terms_days: 30 };
  if (path.endsWith("/statement")) return { total_billed: "100", total_paid: "100", invoices: [{ sale_id: "sale1", series_number: "F001-1", total_amount: "100", paid_amount: "100", pending_balance: "0", created_at: "2026-10-01" }] };
  if (path.endsWith("/history")) return { timeline: [] };
  if (path.endsWith("/segments")) return { matched_segments: [], actual_metrics: {} };
  if (path.endsWith("/credit-check")) return { allowed: true, reason: "Saldo suficiente", available_credit: "4000" };
  if (path.endsWith("/merge/preview")) return { impact: { sales_count: 2, balance_transfer: "30" } };
  if (path.endsWith("/merge")) return { status: "completed" };
  if (path.includes("duplicates/check")) return { exact_matches: [], potential_matches: [], is_exact_duplicate: false };
  if (path.includes("fiscal/validate")) return { valid: true, external_lookup_ready: false };
  if (path.endsWith("/customers/c1")) return customer;
  if (path.includes("/customers")) return { items: [customer], total_count: 1 };
  return { items: [] };
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  window.history.replaceState({}, "", "/?view=customers");
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(respond as typeof apiClient.request);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Recorridos de Clientes después de reorganizar", () => {
  it("abre el listado real desde la aplicación y permite editar sin perder sus valores", async () => {
    vi.spyOn(apiClient, "getMe").mockResolvedValue({ user_id: "user", email: "admin@example.com", role: "company_admin", permissions: ["customers:read", "customers:write"] });
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><OperationsWorkspace /></QueryClientProvider>);
    await screen.findByText(customer.legal_name);
    fireEvent.click(screen.getByRole("button", { name: `Editar ${customer.legal_name}` }));
    const editor = await screen.findByRole("dialog", { name: "Editar cliente" });
    expect((within(editor).getByLabelText("Razón Social / Nombre Completo") as HTMLInputElement).value).toBe(customer.legal_name);
    expect((within(editor).getByLabelText("Límite de Crédito Autorizado") as HTMLInputElement).value).toBe("5000");
    expect(screen.getByRole("button", { name: "Crear cliente" })).toBeTruthy();
  });

  it("guarda una edición con PATCH y conserva los campos comerciales", async () => {
    const saved = vi.fn();
    render(<CustomerEditorDrawer isOpen initialData={customer} onSaved={saved} onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Razón Social / Nombre Completo"), { target: { value: "Comercial Lima actualizada" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cliente" }));
    await waitFor(() => expect(saved).toHaveBeenCalledWith(customer));
    const mutation = vi.mocked(apiClient.request).mock.calls.find(([path, options]) => path === "/api/v1/customers/c1" && options?.method === "PATCH");
    expect(JSON.parse(String(mutation?.[1]?.body))).toMatchObject({ id: "c1", credit_limit: "5000", legal_name: "Comercial Lima actualizada", doc_number: customer.doc_number });
    expect(vi.mocked(apiClient.request).mock.calls.some(([path]) => path.includes("duplicates/check"))).toBe(false);
  });

  it("bloquea un alta duplicada y permite seleccionar el registro existente", async () => {
    vi.mocked(apiClient.request).mockImplementation(async (path, options) => path.includes("duplicates/check") ? { exact_matches: [customer], potential_matches: [], is_exact_duplicate: true } as never : respond(path, options) as never);
    const saved = vi.fn();
    render(<CustomerEditorDrawer isOpen quickMode onSaved={saved} onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Número de Documento/), { target: { value: customer.doc_number } });
    fireEvent.change(screen.getByLabelText("Razón Social / Nombre Completo"), { target: { value: customer.legal_name } });
    await waitFor(() => expect((screen.getByRole("button", { name: "Guardar cliente" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Guardar cliente" }));
    fireEvent.click(await screen.findByRole("button", { name: /Usar este cliente/ }));
    await waitFor(() => expect(saved).toHaveBeenCalledWith(customer));
    expect(vi.mocked(apiClient.request).mock.calls.some(([path, options]) => path === "/api/v1/customers" && options?.method === "POST")).toBe(false);
  });

  it("recupera el borrador al volver a abrir el alta", () => {
    const props = { isOpen: true, onSaved: vi.fn(), onClose: vi.fn() };
    const editor = render(<CustomerEditorDrawer {...props} />);
    fireEvent.change(screen.getByLabelText("Razón Social / Nombre Completo"), { target: { value: "Cliente en borrador" } });
    editor.unmount();
    render(<CustomerEditorDrawer {...props} />);
    expect((screen.getByLabelText("Razón Social / Nombre Completo") as HTMLInputElement).value).toBe("Cliente en borrador");
  });

  it("mantiene contactos, simulación de crédito y repetición de una venta desde la ficha", async () => {
    const onAction = vi.fn();
    render(<CustomerCommercialCard customerId="c1" customerName={customer.legal_name} canWrite allCustomers={[customer]} onClose={vi.fn()} onRefresh={vi.fn()} onAction={onAction} />);
    await screen.findByText("Calidad de ficha");
    fireEvent.click(screen.getByRole("button", { name: "Contactos (1)" }));
    fireEvent.change(screen.getByPlaceholderText("Nombre completo"), { target: { value: "Luis" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar contacto" }));
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith("Contacto registrado"));
    expect(vi.mocked(apiClient.request).mock.calls.some(([path, options]) => path === "/api/v1/customers/c1/contacts" && options?.method === "POST" && JSON.parse(String(options.body)).name === "Luis")).toBe(true);
    await screen.findByText("Ana");
    fireEvent.click(screen.getByRole("button", { name: "Condiciones comerciales" }));
    fireEvent.click(screen.getByRole("button", { name: "Simular crédito" }));
    await screen.findByText("Aprobado: Saldo suficiente");
    fireEvent.click(screen.getByRole("button", { name: "Extracto e Historial" }));
    fireEvent.click(screen.getByRole("button", { name: "Repetir venta" }));
    expect(onAction).toHaveBeenCalledWith("repeat", "sale1");
  });

  it("previsualiza y ejecuta la fusión con los mismos identificadores", async () => {
    const refreshed = vi.fn();
    render(<CustomerCommercialCard customerId="c1" customerName={customer.legal_name} canWrite allCustomers={[customer, { ...customer, id: "c2", legal_name: "Duplicado" }]} onClose={vi.fn()} onRefresh={refreshed} />);
    await screen.findByText("Calidad de ficha");
    fireEvent.click(screen.getByRole("button", { name: "Fusión segura" }));
    fireEvent.change(document.getElementById("duplicate-select-native")!, { target: { value: "c2" } });
    fireEvent.click(screen.getByRole("button", { name: "Previsualizar impacto de la fusión" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar y ejecutar fusión irreversible" }));
    await waitFor(() => expect(refreshed).toHaveBeenCalled());
    for (const path of ["/api/v1/customers/merge/preview", "/api/v1/customers/merge"]) expect(apiClient.request).toHaveBeenCalledWith(path, { method: "POST", body: JSON.stringify({ primary_customer_id: "c1", duplicate_customer_id: "c2" }) });
  });

  it("cancela la búsqueda anterior y conserva el resultado de la búsqueda vigente", async () => {
    let previous: (data: unknown) => void = () => {};
    vi.mocked(apiClient.request).mockImplementation(async path => path.includes("search=anterior") ? new Promise(resolve => { previous = resolve; }) as never : { items: [customer], total_count: 1 } as never);
    const options = { enabled: true, page: 0, pageSize: 25, search: "anterior", revision: 0, onPageChange: vi.fn(), onErrorReset: vi.fn() };
    const hook = renderHook(props => useListadoClientes(props), { initialProps: options });
    const oldSignal = vi.mocked(apiClient.request).mock.calls[0][1]?.signal;
    hook.rerender({ ...options, search: "Comercial Lima" });
    await waitFor(() => expect(hook.result.current.rows).toEqual([customer]));
    expect(oldSignal?.aborted).toBe(true);
    await act(async () => previous({ items: [{ ...customer, id: "obsolete" }], total_count: 1 }));
    expect(hook.result.current.rows).toEqual([customer]);
  });

  it("corrige la página cuando una operación reduce el total de clientes", async () => {
    const onPageChange = vi.fn();
    const onErrorReset = vi.fn();
    const hook = renderHook(() => useListadoClientes({ enabled: true, page: 3, pageSize: 25, search: "", revision: 0, onPageChange, onErrorReset }));
    await waitFor(() => expect(onPageChange).toHaveBeenCalledWith(0));
    expect(hook.result.current.total).toBe(1);
  });
});
