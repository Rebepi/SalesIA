import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { CustomerCommercialCard } from "../src/features/clientes/ficha/CustomerCommercialCard";
import { CustomerEditorDrawer } from "../src/features/clientes/editor/CustomerEditorDrawer";
import { CustomerAnalyticsTab } from "../src/features/clientes/analitica/CustomerAnalyticsTab";
import { ClientesPage } from "../src/features/clientes/pages/ClientesPage";
import disenoAnterior from "./fixtures/clientes-diseno.json";

const toast = { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() };
vi.mock("../src/ui/toast/ToastContext", () => ({ useToast: () => toast }));
const customer = { id: "c1", code: "CLI-01", legal_name: "Cliente de referencia", doc_type: "RUC", doc_number: "20123456789", email: "cliente@example.com", phone: "999888777", credit_limit: "5000", current_balance: "50", is_active: true };
const other = { ...customer, id: "c2", legal_name: "Otro cliente" };
const props = { customerId: customer.id, customerName: customer.legal_name, canWrite: true, allCustomers: [customer, other], onClose: vi.fn(), onRefresh: vi.fn(), onAction: vi.fn() };
const summary = { total_customers: 1, active_in_period: 1, total_revenue: "100", new_customers_count: 1, recurring_customers_count: 0, inactive_customers_count: 0, top_20_concentration_pct: "100" };
const referencias: Record<string, string> = disenoAnterior;

async function respond(path: string) {
  if (path.includes("/analytics/customers")) return { summary, items: [{ customer_id: "c1", code: customer.code, legal_name: customer.legal_name, customer_type: "new", orders_count: 2, total_revenue: "100", recency_days: 3, average_ticket: "50", revenue_share_pct: "100" }], cohorts: [{ cohort: "2026-10", size: 1, retention_pct: ["100", "80"] }] };
  if (path.endsWith("/quality")) return { score_percentage: 80, missing_fields: [], alerts: ["Completar dirección"], blocking_purchases: false };
  if (path.endsWith("/contacts")) return [{ id: "contact1", name: "Ana", role: "Compras", email: "ana@example.com", phone: "999222333", is_primary: true }];
  if (path.endsWith("/addresses")) return [{ id: "address1", address_type: "shipping", address_line: "Av. Lima 123", district: "Lima", city: "Lima", is_primary: true }];
  if (path.endsWith("/commercial-terms")) return { payment_terms_days: 30, is_credit_blocked: false, price_list_id: "ESTANDAR" };
  if (path.endsWith("/statement")) return { total_billed: "100", total_paid: "50", invoices: [{ sale_id: "sale1", series_number: "F001-000001", status: "confirmed", total_amount: "100", paid_amount: "50", pending_balance: "50", created_at: "2026-10-01T10:00:00Z" }] };
  if (path.endsWith("/notes")) return [{ id: "note1", content: "Cliente preferente", created_at: "2026-10-01T10:00:00Z", is_sensitive: false }];
  if (path.endsWith("/segments")) return { matched_segments: [{ id: "seg1", name: "Frecuente" }], actual_metrics: {} };
  if (path.endsWith("/history")) return { timeline: [{ id: "sale1", type: "sale", reference: "F001-000001", date: "2026-10-01T10:00:00Z", amount: "100" }] };
  if (path.endsWith("/companies/current")) return { base_currency: "PEN" };
  if (path.endsWith("/customers/c1")) return customer;
  if (path.includes("fiscal/validate")) return { valid: true, external_lookup_ready: false };
  if (path.includes("duplicates/check")) return { exact_matches: [], potential_matches: [], is_exact_duplicate: false };
  return { items: [] };
}

function markup() {
  const ids = new Map<string, string>();
  return document.body.innerHTML.replace(/:r[0-9a-z]+:|info-tooltip-r[0-9a-z]+/g, id => {
    if (!ids.has(id)) ids.set(id, `:id${ids.size}:`);
    return ids.get(id)!;
  }).replace(/\s+</g, "<").replace(/>\s+/g, ">");
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  vi.spyOn(apiClient, "request").mockImplementation(respond as typeof apiClient.request);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); document.documentElement.className = ""; });

describe("Paridad con las fuentes anteriores de Clientes", () => {
  for (const theme of ["light", "dark"]) {
    for (const canWrite of [true, false]) {
      for (const tab of ["Resumen y Calidad", "Contactos (1)", "Direcciones (1)", "Condiciones comerciales", "Extracto e Historial", "Notas (1)", "Fusión segura"]) {
        it(`${theme}, escritura ${canWrite}, pestaña ${tab}`, async () => {
          document.documentElement.className = theme;
          const expected = referencias[`${theme}-${canWrite}-${tab}`];
          render(<CustomerCommercialCard {...props} canWrite={canWrite} />);
          await screen.findByText("Calidad de ficha");
          fireEvent.click(screen.getByRole("button", { name: tab }));
          expect(markup()).toBe(expected);
        });
      }
    }
    for (const mode of ["quick", "full", "edit"]) {
      it(`${theme}, editor ${mode}`, async () => {
        document.documentElement.className = theme;
        const editorProps = { isOpen: true, quickMode: mode === "quick", initialData: mode === "edit" ? customer : null, onClose: vi.fn(), onSaved: vi.fn() };
        const expected = referencias[`${theme}-${mode}`];
        render(<CustomerEditorDrawer {...editorProps} />);
        expect(markup()).toBe(expected);
      });
    }
    it(`${theme}, analítica con resultados`, async () => {
      document.documentElement.className = theme;
      const expected = referencias[`${theme}-analitica`];
      render(<CustomerAnalyticsTab />);
      await screen.findByText(customer.legal_name);
      expect(markup()).toBe(expected);
    });
  }

  it("conserva el formulario al validar el documento", async () => {
    const expected = referencias["validacion-documento"];
    render(<CustomerEditorDrawer isOpen quickMode onClose={vi.fn()} onSaved={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Número de Documento/), { target: { value: customer.doc_number } });
    await screen.findByText("Documento validado localmente.");
    await waitFor(() => expect(markup()).toBe(expected));
  });

  for (const canWrite of [true, false]) {
    for (const state of ["active", "archived", "empty", "loading", "error"]) {
      it(`listado ${state}, escritura ${canWrite}`, () => {
        const pageProps = { rows: ["empty", "loading", "error"].includes(state) ? [] : [{ ...customer, is_active: state === "active" }], total: state === "empty" ? 0 : 1, loading: state === "loading", search: "", page: 0, pageSize: 50, error: state === "error" ? "No se pudo cargar" : "", editorOpen: false, confirmationOpen: false, canWrite, setSearch: vi.fn(), setPage: vi.fn(), setPageSize: vi.fn(), onRefresh: vi.fn(), openEntity: vi.fn(), setSelectedCustomer: vi.fn(), setConfirm: vi.fn() };
        const expected = referencias[`listado-${state}-${canWrite}`];
        render(<ClientesPage {...pageProps} />);
        expect(markup()).toBe(expected);
      });
    }
  }
});
