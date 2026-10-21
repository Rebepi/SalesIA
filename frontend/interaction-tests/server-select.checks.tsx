import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiClient } from "../src/api/client";
import { CustomSelect } from "../src/ui/components/CustomSelect";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("consulta solo al abrir, pagina en servidor y no renderiza las 5000 opciones locales", async () => {
  const request = vi.spyOn(apiClient, "request").mockImplementation(async (path: string) => {
    const params = new URL(path, "http://localhost").searchParams;
    const offset = Number(params.get("offset") || 0);
    expect(params.get("limit")).toBe("20");
    return { items: Array.from({ length: 20 }, (_, index) => ({ value: String(offset + index + 1), label: `Vendedor ${offset + index + 1}` })), has_more: true, total_count: 5000 } as never;
  });
  render(<CustomSelect aria-label="Vendedor" remote={{ resource: "sales_reps" }}><option value="">Seleccionar</option>{Array.from({ length: 5000 }, (_, index) => <option key={index} value={String(index + 1)}>Local {index}</option>)}</CustomSelect>);
  expect(request).not.toHaveBeenCalled();
  expect(document.querySelectorAll("select option")).toHaveLength(1);
  fireEvent.click(screen.getByRole("combobox", { name: "Vendedor" }));
  await screen.findByRole("option", { name: "Vendedor 20" });
  expect(document.querySelectorAll("select option")).toHaveLength(21);
  fireEvent.click(screen.getByRole("button", { name: "Cargar más" }));
  await screen.findByRole("option", { name: "Vendedor 40" });
  expect(request.mock.calls.some(([path]) => String(path).includes("offset=20"))).toBe(true);
});

it("busca en servidor y conserva la selección al cerrar y enviar el formulario", async () => {
  const change = vi.fn();
  const request = vi.spyOn(apiClient, "request").mockImplementation(async (path: string) => {
    const params = new URL(path, "http://localhost").searchParams;
    return { items: params.get("search") === "4999" || params.get("ids") === "4999" ? [{ value: "4999", label: "Vendedor 4999" }] : [], has_more: false } as never;
  });
  render(<form><CustomSelect name="rep_id" required aria-label="Vendedor" remote={{ resource: "sales_reps" }} onChange={change}><option value="">Seleccionar</option></CustomSelect></form>);
  fireEvent.click(screen.getByRole("combobox", { name: "Vendedor" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Buscar opciones" }), { target: { value: "4999" } });
  await screen.findByRole("option", { name: "Vendedor 4999" });
  fireEvent.keyDown(screen.getByRole("textbox", { name: "Buscar opciones" }), { key: "Enter" });
  expect(change).toHaveBeenCalledOnce();
  expect(screen.queryByRole("listbox")).toBeNull();
  await waitFor(() => expect(new FormData(document.querySelector("form")!).get("rep_id")).toBe("4999"));
  expect(screen.getByRole("combobox", { name: "Vendedor" }).textContent).toContain("Vendedor 4999");
  expect(request.mock.calls.some(([path]) => String(path).includes("search=4999"))).toBe(true);
});

it("mantiene varias selecciones y sus IDs en formularios de aprobadores", async () => {
  vi.spyOn(apiClient, "request").mockImplementation(async () => ({ items: [{ value: "ana", label: "Ana" }, { value: "luis", label: "Luis" }], has_more: false }) as never);
  function Form() {
    const [values, setValues] = useState<string[]>([]);
    return <form><CustomSelect name="approver_ids" aria-label="Aprobadores" multiple value={values} onChange={event => setValues(Array.from(event.target.selectedOptions, option => option.value))} remote={{ resource: "people" }} /></form>;
  }
  render(<Form />);
  fireEvent.click(screen.getByRole("combobox", { name: "Aprobadores" }));
  fireEvent.click(await screen.findByRole("option", { name: "Ana" }));
  fireEvent.click(screen.getByRole("option", { name: "Luis" }));
  await waitFor(() => expect(new FormData(document.querySelector("form")!).getAll("approver_ids")).toEqual(["ana", "luis"]));
  expect(screen.getByRole("combobox", { name: "Aprobadores" }).textContent).toContain("2 seleccionados");
});
