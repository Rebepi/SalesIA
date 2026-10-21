import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { ReturnPolicyPanel } from "../src/features/devoluciones/components/ReturnPolicyPanel";
import { Panel1 as Sidebar } from "../src/app/workspace/sections/OperationsWorkspace/Panel1";
import { apiClient } from "../src/api/client";
import { viewFromUrl } from "../src/app/workspace/support/OperationsWorkspace";

afterEach(() => { cleanup(); vi.restoreAllMocks(); window.history.replaceState({}, "", "/"); });
const rule = { returnable: true, days: 30, allowed_conditions: ["unused"], allowed_packaging: ["sealed"], evidence_required: false, allow_exceptions: true, retention_percentage: "0", retention_description: "" };

it("ubica políticas únicamente en Configuración y conserva acceso de consulta", () => {
  render(<Sidebar sidebarCollapsed={false} setSidebarHoveredTooltip={vi.fn()} can={permission => permission === "payments:read"} view="settings_return_policy" navigate={vi.fn()} />);
  const settings = screen.getByRole("list", { name: "Configuración" });
  expect(within(settings).getByRole("button", { name: "Políticas de devolución" }).getAttribute("aria-current")).toBe("page");
  expect(within(settings).queryByRole("button", { name: "Empresa" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Devoluciones y reembolsos" }));
  expect(within(screen.getByRole("list", { name: "Devoluciones y reembolsos" })).queryByRole("button", { name: "Políticas de devolución" })).toBeNull();
  window.history.replaceState({}, "", "/?view=refunds_policy");
  expect(viewFromUrl()).toBe("settings_return_policy");
});

it("usa switches y chips y conserva el contrato de guardado", async () => {
  const policy = { version: 2, default_rule: rule, rules: {}, can_manage: true };
  const request = vi.spyOn(apiClient, "request").mockResolvedValue(policy as never);
  const { container } = render(<ReturnPolicyPanel standalone />);
  const evidence = await screen.findByRole("switch", { name: "Requiere evidencia documentada" });
  expect(container.querySelector('input[type="checkbox"]')).toBeNull();
  expect(screen.getAllByRole("switch")).toHaveLength(6);
  fireEvent.click(evidence);
  expect(evidence.getAttribute("aria-checked")).toBe("true");
  fireEvent.click(screen.getByRole("button", { name: "Usado", exact: true }));
  fireEvent.click(within(screen.getByRole("group", { name: "Empaque permitido" })).getByRole("button", { name: "No aplica" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Motivo del cambio" }), { target: { value: "Actualización documentada de condiciones" } });
  fireEvent.submit((screen.getByRole("button", { name: "Guardar nueva versión" }) as HTMLButtonElement).form!);
  await waitFor(() => expect(request.mock.calls.some(([, options]) => options?.method === "PUT")).toBe(true));
  const mutation = request.mock.calls.find(([, options]) => options?.method === "PUT");
  const body = JSON.parse(String(mutation?.[1]?.body));
  expect(body.version).toBe(2);
  expect(body.default_rule.evidence_required).toBe(true);
  expect(body.default_rule.allowed_conditions).toEqual(["unused", "used"]);
  expect(body.default_rule.allowed_packaging).toEqual(["not_applicable"]);
  expect(body.reason).toBe("Actualización documentada de condiciones");
});

it("deshabilita switches para consulta y operaciones bloqueadas", async () => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ version: 1, default_rule: rule, rules: {}, can_manage: false } as never);
  const { rerender } = render(<ReturnPolicyPanel standalone />);
  const toggle = await screen.findByRole("switch", { name: "Admite devolución comercial" });
  expect((toggle as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(toggle);
  expect(toggle.getAttribute("aria-checked")).toBe("true");
  expect(screen.queryByRole("button", { name: "Guardar nueva versión" })).toBeNull();
  rerender(<ReturnPolicyPanel standalone canWrite={false} />);
  expect((screen.getByRole("switch", { name: "Requiere evidencia documentada" }) as HTMLButtonElement).disabled).toBe(true);
});

it("revela las condiciones de cada tipo al activar su switch y conserva la regla general", async () => {
  const request = vi.spyOn(apiClient, "request").mockResolvedValue({ version: 3, default_rule: rule, rules: {}, can_manage: true } as never);
  render(<ReturnPolicyPanel standalone />);
  await screen.findByRole("region", { name: "Regla general" });
  expect(screen.queryByRole("tablist")).toBeNull();
  const products = screen.getByRole("region", { name: "Condiciones de productos" });
  const toggle = within(products).getByRole("switch", { name: "Usar condiciones propias para productos" });
  expect(within(products).queryByRole("spinbutton")).toBeNull();
  fireEvent.click(toggle);
  fireEvent.change(within(products).getByRole("spinbutton", { name: "Plazo desde la venta (días calendario)" }), { target: { value: "60" } });
  expect((within(screen.getByRole("region", { name: "Regla general" })).getByRole("spinbutton", { name: "Plazo desde la venta (días calendario)" }) as HTMLInputElement).value).toBe("30");
  fireEvent.click(toggle);
  expect(within(products).queryByRole("spinbutton")).toBeNull();
  fireEvent.click(toggle);
  expect((within(products).getByRole("spinbutton", { name: "Plazo desde la venta (días calendario)" }) as HTMLInputElement).value).toBe("30");
  expect(request).toHaveBeenCalledTimes(1);
  fireEvent.change(within(products).getByRole("spinbutton", { name: "Plazo desde la venta (días calendario)" }), { target: { value: "60" } });
  fireEvent.change(screen.getByRole("textbox", { name: "Motivo del cambio" }), { target: { value: "Plazo específico para productos" } });
  fireEvent.submit((screen.getByRole("button", { name: "Guardar nueva versión" }) as HTMLButtonElement).form!);
  await waitFor(() => expect(request.mock.calls.some(([, options]) => options?.method === "PUT")).toBe(true));
  const body = JSON.parse(String(request.mock.calls.find(([, options]) => options?.method === "PUT")?.[1]?.body));
  expect(body.default_rule.days).toBe(30);
  expect(body.rules.product.days).toBe(60);
  expect(body.rules.service).toBeUndefined();
  expect(body.rules.kit).toBeUndefined();
});

it("condiciona los campos a la devolución y muestra el concepto solo con retención", async () => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ version: 1, default_rule: rule, rules: {}, can_manage: true } as never);
  render(<ReturnPolicyPanel standalone />);
  const general = await screen.findByRole("region", { name: "Regla general" });
  expect(screen.queryByRole("textbox", { name: "Motivo del cambio" })).toBeNull();
  expect(within(general).queryByRole("textbox", { name: "Concepto de la retención" })).toBeNull();
  expect(screen.getAllByText("Usa la regla general: 30 días, sin retención.")).toHaveLength(3);
  const retention = within(general).getByRole("spinbutton", { name: "Retención del valor devuelto (%)" });
  fireEvent.change(retention, { target: { value: "5" } });
  expect((within(general).getByRole("textbox", { name: "Concepto de la retención" }) as HTMLInputElement).required).toBe(true);
  expect(screen.getByRole("textbox", { name: "Motivo del cambio" })).toBeTruthy();
  fireEvent.change(retention, { target: { value: "0" } });
  expect(screen.queryByRole("textbox", { name: "Motivo del cambio" })).toBeNull();
  fireEvent.click(within(general).getByRole("switch", { name: "Admite devolución comercial" }));
  expect(within(general).queryByRole("spinbutton")).toBeNull();
  fireEvent.click(within(general).getByRole("switch", { name: "Admite devolución comercial" }));
  expect((within(general).getByRole("spinbutton", { name: "Plazo desde la venta (días calendario)" }) as HTMLInputElement).value).toBe("30");
});

it("hace No aplica excluyente, mantiene una opción mínima y oculta empaque en servicios", async () => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ version: 1, default_rule: rule, rules: {}, can_manage: true } as never);
  render(<ReturnPolicyPanel standalone />);
  const general = await screen.findByRole("region", { name: "Regla general" });
  const chips = within(general).getByRole("group", { name: "Estado del artículo permitido" });
  fireEvent.click(within(chips).getByRole("button", { name: "No aplica" }));
  expect(within(chips).getByRole("button", { name: "Sin uso" }).getAttribute("aria-pressed")).toBe("false");
  fireEvent.click(within(chips).getByRole("button", { name: "Usado" }));
  expect(within(chips).getByRole("button", { name: "No aplica" }).getAttribute("aria-pressed")).toBe("false");
  fireEvent.click(within(chips).getByRole("button", { name: "Usado" }));
  expect(within(chips).getByRole("button", { name: "Usado" }).getAttribute("aria-pressed")).toBe("true");
  const services = screen.getByRole("region", { name: "Condiciones de servicios" });
  fireEvent.click(within(services).getByRole("switch", { name: "Usar condiciones propias para servicios" }));
  expect(within(services).queryByRole("group", { name: "Empaque permitido" })).toBeNull();
  expect(within(services).getByRole("group", { name: "Estado del artículo permitido" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Consultar historial" }).closest("form")).toBeNull();
  const save = screen.getByRole("button", { name: "Guardar nueva versión" }) as HTMLButtonElement;
  expect(save.form).toBeTruthy();
  expect(save.closest(".return-policy-savebar")).toBeTruthy();
});

function mockDialogs() {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
}

it("abre el historial en un modal, muestra carga y vacío y conserva los cambios pendientes", async () => {
  mockDialogs();
  let resolveHistory!: (value: unknown) => void;
  vi.spyOn(apiClient, "request").mockImplementation((path) => path.endsWith("/history") ? new Promise(resolve => { resolveHistory = resolve; }) as never : Promise.resolve({ version: 0, default_rule: rule, rules: {}, can_manage: true }) as never);
  render(<ReturnPolicyPanel standalone />);
  fireEvent.click(await screen.findByRole("switch", { name: "Requiere evidencia documentada" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Motivo del cambio" }), { target: { value: "Conservar este motivo" } });
  const open = screen.getByRole("button", { name: "Consultar historial" });
  open.focus();
  fireEvent.click(open);
  const dialog = await screen.findByRole("dialog", { name: "Historial de versiones" });
  expect(within(dialog).getByText("Cargando historial…")).toBeTruthy();
  resolveHistory([]);
  await within(dialog).findByText("Aún no hay versiones guardadas");
  fireEvent(dialog, new Event("cancel", { cancelable: true }));
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(document.activeElement).toBe(open);
  expect((screen.getByRole("textbox", { name: "Motivo del cambio" }) as HTMLTextAreaElement).value).toBe("Conservar este motivo");
  expect(screen.getByRole("switch", { name: "Requiere evidencia documentada" }).getAttribute("aria-checked")).toBe("true");
});

it("permite reintentar el historial y consultar los valores de una versión guardada", async () => {
  mockDialogs();
  let attempts = 0;
  const saved = { version: 4, default_rule: { ...rule, days: 60 }, rules: { service: rule }, reason: "Ampliar plazo documentado", actor: "admin@example.com", at: "2026-10-21T15:00:00Z" };
  vi.spyOn(apiClient, "request").mockImplementation(path => {
    if (!path.endsWith("/history")) return Promise.resolve({ ...saved, can_manage: true }) as never;
    attempts += 1;
    return (attempts === 1 ? Promise.reject({ detail: "Error temporal" }) : Promise.resolve([saved])) as never;
  });
  render(<ReturnPolicyPanel standalone />);
  fireEvent.click(await screen.findByRole("button", { name: "Consultar historial" }));
  const dialog = await screen.findByRole("dialog", { name: "Historial de versiones" });
  await within(dialog).findByRole("alert");
  fireEvent.click(within(dialog).getByRole("button", { name: "Reintentar" }));
  fireEvent.click(await within(dialog).findByText("Versión 4"));
  expect(within(dialog).getByText("Ampliar plazo documentado")).toBeTruthy();
  expect(within(dialog).getByText("Admite devolución: 60 días calendario")).toBeTruthy();
  expect(within(dialog).getByText("Servicios")).toBeTruthy();
  fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar historial" }));
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("ofrece ayuda interactiva sin modificar los controles ni depender del tooltip del navegador", async () => {
  vi.spyOn(apiClient, "request").mockResolvedValue({ version: 1, default_rule: rule, rules: {}, can_manage: true } as never);
  const { container } = render(<ReturnPolicyPanel standalone />);
  const help = await screen.findByRole("button", { name: "Información sobre Admite devolución comercial" });
  fireEvent.click(help);
  expect(help.getAttribute("aria-expanded")).toBe("true");
  expect(screen.getByLabelText("Ayuda: Admite devolución comercial")).toBeTruthy();
  expect(screen.getByRole("switch", { name: "Admite devolución comercial" }).getAttribute("aria-checked")).toBe("true");
  fireEvent.keyDown(help, { key: "Escape" });
  expect(help.getAttribute("aria-expanded")).toBe("false");
  fireEvent.keyDown(help, { key: "Enter" });
  expect(help.getAttribute("aria-expanded")).toBe("true");
  for (const label of ["Plazo desde la venta (días calendario)", "Estado del artículo permitido", "Empaque permitido", "Retención del valor devuelto (%)", "Requiere evidencia documentada", "Admite excepción o exoneración autorizada", "Excepciones por tipo", "Condiciones de servicios"]) {
    expect(screen.getByRole("button", { name: `Información sobre ${label}` })).toBeTruthy();
  }
  expect(container.querySelector("[title]")).toBeNull();
  expect(container.querySelector('button[role="switch"] [role="button"]')).toBeNull();
});
