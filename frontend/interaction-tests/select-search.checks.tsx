import React from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { CustomSelect } from "../src/ui/components/CustomSelect";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("filters accented options and selects the matching native value by keyboard", () => {
  const change = vi.fn();
  render(<CustomSelect searchable aria-label="Almacén" onChange={change}><option value="lima">Lima</option><option value="huanuco">Huánuco</option><option value="cusco" disabled>Cusco</option></CustomSelect>);
  const trigger = screen.getByRole("combobox", { name: "Almacén" });
  fireEvent.click(trigger);
  const search = screen.getByRole("textbox", { name: "Buscar opciones" });
  fireEvent.blur(trigger, { relatedTarget: search });
  fireEvent.change(search, { target: { value: "huanuco" } });
  expect(screen.getAllByRole("option")).toHaveLength(1);
  fireEvent.keyDown(search, { key: "Enter" });
  expect(change).toHaveBeenCalledOnce();
  expect(document.querySelector("select")?.value).toBe("huanuco");
  expect(screen.queryByRole("listbox")).toBeNull();
});

it("shows an empty result and resets search on reopening", () => {
  render(<CustomSelect searchable aria-label="Sede"><option value="1">Central</option><option value="2">Norte</option></CustomSelect>);
  const trigger = screen.getByRole("combobox", { name: "Sede" });
  fireEvent.click(trigger);
  const search = screen.getByRole("textbox");
  fireEvent.change(search, { target: { value: "inexistente" } });
  expect(screen.getByText("No hay opciones coincidentes")).toBeTruthy();
  fireEvent.keyDown(search, { key: "Escape" });
  fireEvent.click(trigger);
  expect(screen.getAllByRole("option")).toHaveLength(2);
});
