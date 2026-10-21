import type { ComponentProps } from "react";
import { SeccionReglas } from "../src/features/organizacion/sections/CompanySettingsWorkspaceTab/SeccionReglas";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { BusinessPoliciesEditor } from "../src/features/organizacion/components/BusinessPoliciesEditor";
import { AccountingPeriodsEditor } from "../src/features/organizacion/components/AccountingPeriodsEditor";
import { SettingSwitch } from "../src/ui/components/SettingsControls";
import { apiClient } from "../src/api/client";
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const settings = { version: 3, pricing_policy: { default_volume_discounts_enabled: true, volume_tiers: [{ min_quantity: "10", discount_percentage: "0.05" }], minimum_margin_percentage: "0", maximum_manual_discount_percentage: "0" }, commission_policy: { version: 2, tiers: [{ minimum_attainment: "0", rate: "0" }, { minimum_attainment: "120", rate: "0.07" }] }, replenishment_policy: { default_lead_time_days: 7, history_days: 30 } };
it("muestra switches y ayudas, evita decimales artificiales y conserva el contrato de guardado", async () => {
  const request = vi.spyOn(apiClient, "request").mockResolvedValue(settings as never);
  render(<BusinessPoliciesEditor canWrite />);
  const toggle = await screen.findByRole("switch", { name: "Aplicar escalas generales cuando el producto no tenga escalas propias" });
  expect(screen.queryByRole("checkbox")).toBeNull();
  const commission = screen.getByRole("group", { name: "Comisión por cumplimiento · versión 2" });
  const percentages = within(commission).getAllByRole("spinbutton", { name: "Porcentaje" }) as HTMLInputElement[];
  expect(percentages[1].value).toBe("7");
  const help = screen.getByRole("button", { name: "Información sobre Aplicar escalas generales cuando el producto no tenga escalas propias" });
  fireEvent.click(help);
  expect((toggle as HTMLInputElement).checked).toBe(true);
  expect(screen.getByLabelText("Ayuda: Aplicar escalas generales cuando el producto no tenga escalas propias")).toBeTruthy();
  fireEvent.click(toggle);
  fireEvent.click(screen.getByRole("button", { name: "Guardar estas políticas" }));
  await waitFor(() => expect(request.mock.calls.some(([, options]) => options?.method === "PATCH")).toBe(true));
  const body = JSON.parse(String(request.mock.calls.find(([, options]) => options?.method === "PATCH")?.[1]?.body));
  expect(body.pricing_policy.default_volume_discounts_enabled).toBe(false);
  expect(body.commission_policy.tiers[1].rate).toBe("0.07");
  expect(screen.getByRole("button", { name: "Información sobre Tolerancia de precio unitario %" })).toBeTruthy();
});
it("respeta permisos y la selección de módulos mediante switches con ayudas", async () => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ version: 1, modules: { sales: "Ventas", inventory: "Inventario" }, controls: {}, closed_until: null, closed_periods: [], legacy_reopenings: [], business_date: "2026-10-21" } as never);
  const { rerender } = render(<AccountingPeriodsEditor canWrite />);
  const sales = await screen.findByRole("switch", { name: "Ventas" });
  expect((sales as HTMLInputElement).checked).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Información sobre Ventas" }));
  expect((sales as HTMLInputElement).checked).toBe(true);
  fireEvent.click(sales);
  expect((sales as HTMLInputElement).checked).toBe(false);
  expect(screen.getByRole("combobox", { name: "Módulo" })).toBeTruthy();
  rerender(<AccountingPeriodsEditor canWrite={false} />);
  expect((screen.getByRole("switch", { name: "Ventas" }) as HTMLInputElement).disabled).toBe(true);
  expect((screen.getByRole("button", { name: "Consultar bloqueos y pendientes" }) as HTMLButtonElement).disabled).toBe(true);
});
it("conserva validación obligatoria y FormData de un reconocimiento presentado como switch", () => {
  render(<form data-testid="form"><SettingSwitch label="Reconocer pendientes" description="Los compromisos continúan abiertos." name="acknowledge_pending" required /></form>);
  const form = screen.getByTestId("form") as HTMLFormElement;
  const toggle = screen.getByRole("switch", { name: "Reconocer pendientes" }) as HTMLInputElement;
  expect(toggle.validity.valueMissing).toBe(true);
  fireEvent.click(toggle);
  expect(toggle.validity.valueMissing).toBe(false);
  expect(new FormData(form).get("acknowledge_pending")).toBe("on");
});

it("organiza las políticas en pestañas accesibles y conserva borradores al navegar", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (path === "/api/v1/companies/current/settings") return settings as never;
    if (path === "/api/v1/organization/module-periods") return { version: 1, modules: {}, controls: {}, closed_until: null, closed_periods: [], legacy_reopenings: [], business_date: "2026-10-21" } as never;
    return [] as never;
  });
  const props = { saveCommercialSettings: vi.fn(), settings: null, taxRate: "0.18", setTaxRate: vi.fn(), canWrite: true, inputClass: "", roundingMode: "ROUND_HALF_EVEN", setRoundingMode: vi.fn(), creditLimitStrict: true, setCreditLimitStrict: vi.fn(), taxIncluded: false, setTaxIncluded: vi.fn(), allowCreditSales: true, setAllowCreditSales: vi.fn(), holdExpirationValue: 2, setHoldExpirationValue: vi.fn(), holdExpirationUnit: "HOURS", setHoldExpirationUnit: vi.fn(), saving: false, taxRules: [], setRuleDraft: vi.fn(), saveTaxRule: vi.fn(), ruleDraft: { code: "", rate: "0.18", name: "", is_active: true } } as unknown as ComponentProps<typeof SeccionReglas>;
  render(<SeccionReglas {...props} />);
  expect(screen.getAllByRole("tab")).toHaveLength(5);
  expect(screen.getAllByRole("tabpanel")).toHaveLength(1);
  expect(screen.getByRole("tabpanel", { name: "Ventas y crédito" })).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Crédito y precios del catálogo" })).toBeTruthy();
  fireEvent.click(screen.getByRole("tab", { name: "Precios y abastecimiento" }));
  const lead = await screen.findByRole("spinbutton", { name: "Plazo de reposición predeterminado en días" });
  fireEvent.change(lead, { target: { value: "12" } });
  fireEvent.click(screen.getByRole("tab", { name: "Reglas fiscales" }));
  expect(screen.queryByRole("spinbutton", { name: "Plazo de reposición predeterminado en días" })).toBeNull();
  expect(screen.getByRole("textbox", { name: "Código de regla fiscal" })).toBeTruthy();
  fireEvent.click(screen.getByRole("tab", { name: "Precios y abastecimiento" }));
  expect((screen.getByRole("spinbutton", { name: "Plazo de reposición predeterminado en días" }) as HTMLInputElement).value).toBe("12");
  fireEvent.keyDown(screen.getByRole("tab", { name: "Precios y abastecimiento" }), { key: "End" });
  expect(screen.getByRole("tab", { name: "Cierres y reaperturas" }).getAttribute("aria-selected")).toBe("true");
  expect(screen.getAllByRole("tabpanel")).toHaveLength(1);
});

it("abre las consultas de cierres en modales con carga, reintento y restauración del foco", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  let failed = false;
  vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).includes("/history?")) {
      if (!failed) { failed = true; throw { detail: "Error temporal" }; }
      return [{ version: 1, action: "close", actor: "Administrador", at: "2026-10-21", reason: "Cierre de ventas revisado" }] as never;
    }
    if (String(path).includes("/changes?")) return [] as never;
    return { version: 1, modules: { sales: "Ventas" }, controls: {}, closed_until: null, closed_periods: [], legacy_reopenings: [], business_date: "2026-10-21" } as never;
  });
  render(<AccountingPeriodsEditor canWrite />);
  const trigger = await screen.findByRole("button", { name: "Historial de controles" });
  trigger.focus();
  fireEvent.click(trigger);
  const modal = await screen.findByRole("dialog", { name: "Historial de controles" });
  await within(modal).findByRole("alert");
  fireEvent.click(within(modal).getByRole("button", { name: "Reintentar" }));
  expect(await within(modal).findByText(/Cierre de ventas revisado/)).toBeTruthy();
  fireEvent(modal, new Event("cancel", { cancelable: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(trigger);
  fireEvent.click(screen.getByRole("button", { name: "Operaciones efectuadas con reapertura" }));
  const changes = await screen.findByRole("dialog", { name: "Operaciones efectuadas con reapertura" });
  expect(await within(changes).findByText("No hay operaciones registradas para esta página.")).toBeTruthy();
});
