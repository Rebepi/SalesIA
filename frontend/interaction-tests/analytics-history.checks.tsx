import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { AnalyticsHistoryWorkspaceTab } from "../src/features/analitica/components/AnalyticsHistoryWorkspaceTab";
import { apiClient } from "../src/api/client";
const record = (id: string, extra = {}) => ({ id, name: `Análisis ${id}`, dataset_id: "dataset-a", dataset_version: 2, variable_name: "total_amount", analysis_type: "mean", result: { count: 2, mean: "15.000000", didactic_explanation: { formula: "suma / cantidad" } }, algorithm_version: "v1.2.0", created_by: "analista", created_at: "2026-10-21T12:00:00Z", status: "completed", ...extra });
beforeEach(() => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it("hace visible la comparación, conserva selecciones entre páginas y muestra resultados completos", async () => {
  const request = vi.spyOn(apiClient, "request").mockImplementation(async path => {
    if (String(path).includes("offset=25")) return { items: [record("b")], count: 26 } as never;
    return { items: [record("a")], count: 26 } as never;
  });
  render(<AnalyticsHistoryWorkspaceTab />);
  const compare = screen.getByRole("button", { name: "Comparar ejecuciones" });
  expect((compare as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(await screen.findByRole("checkbox", { name: "Comparar Análisis a (a)" }));
  fireEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
  fireEvent.click(await screen.findByRole("checkbox", { name: "Comparar Análisis b (b)" }));
  fireEvent.click(compare);
  const dialog = await screen.findByRole("dialog", { name: "Comparativa de ejecuciones" });
  expect(within(dialog).getAllByText("15.000000").length).toBeGreaterThan(0);
  expect(within(dialog).getAllByText(/suma \/ cantidad/)).toHaveLength(2);
  expect(request.mock.calls.some(([path]) => String(path).includes("limit=25&offset=25"))).toBe(true);
  fireEvent(dialog, new Event("cancel", { cancelable: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
});
it("consulta el detalle real y repite con la misma versión sin modificar el original", async () => {
  const request = vi.spyOn(apiClient, "request").mockImplementation(async (path, options) => {
    if (options?.method === "POST") return record("nuevo") as never;
    if (path === "/api/v1/analyses/a") return record("a", { explanation: "Detalle recuperado del servidor" }) as never;
    return { items: [record("a")], count: 1 } as never;
  });
  render(<AnalyticsHistoryWorkspaceTab />);
  fireEvent.click(await screen.findByRole("button", { name: "Ver detalle de Análisis a" }));
  const dialog = await screen.findByRole("dialog", { name: "Análisis a" });
  expect(await within(dialog).findByText("Detalle recuperado del servidor")).toBeTruthy();
  fireEvent.click(within(dialog).getByRole("button", { name: "Cerrar detalle" }));
  fireEvent.click(screen.getByRole("button", { name: "Repetir Análisis a" }));
  await screen.findByRole("dialog", { name: "Análisis nuevo" });
  const mutation = request.mock.calls.find(([, options]) => options?.method === "POST");
  expect(mutation?.[0]).toBe("/api/v1/analyses/a/repeat");
  expect(JSON.parse(String(mutation?.[1]?.body))).toEqual({ new_version: 2 });
  expect(screen.getByText(/La ejecución original se conserva/)).toBeTruthy();
});
it("bloquea reejecuciones sin dataset o canceladas y respeta la consulta sin permiso de escritura", async () => {
  const request = vi.spyOn(apiClient, "request").mockResolvedValue({ items: [record("manual", { dataset_id: null }), record("cancelado", { status: "cancelled", result: null })], count: 2 } as never);
  const { rerender } = render(<AnalyticsHistoryWorkspaceTab />);
  expect((await screen.findByRole("button", { name: "Repetir Análisis manual" }) as HTMLButtonElement).disabled).toBe(true);
  expect((screen.getByRole("button", { name: "Repetir Análisis cancelado" }) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Repetir Análisis manual" }));
  expect(request.mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
  rerender(<AnalyticsHistoryWorkspaceTab canWrite={false} />);
  expect(screen.queryByRole("button", { name: /Repetir Análisis/ })).toBeNull();
  expect(screen.getByRole("button", { name: "Ver detalle de Análisis manual" })).toBeTruthy();
});
it("permite reintentar la carga y muestra errores de reejecución sin ocultar el historial", async () => {
  let first = true;
  vi.spyOn(apiClient, "request").mockImplementation(async (_path, options) => {
    if (options?.method === "POST") throw { detail: "El dataset ya no está disponible" };
    if (first) { first = false; throw { detail: "Conexión interrumpida" }; }
    return { items: [record("a")], count: 1 } as never;
  });
  render(<AnalyticsHistoryWorkspaceTab />);
  await screen.findByRole("alert");
  fireEvent.click(screen.getByRole("button", { name: "Reintentar", exact: true }));
  fireEvent.click(await screen.findByRole("button", { name: "Repetir Análisis a" }));
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("El dataset ya no está disponible"));
  expect(screen.getByRole("button", { name: "Ver detalle de Análisis a" })).toBeTruthy();
});
