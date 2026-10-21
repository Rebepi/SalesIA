import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QuotationRowActions } from "../src/features/cotizaciones/components/QuotationRowActions";

afterEach(cleanup);
const callbacks = () => ({ onAccept: vi.fn(), onVersion: vi.fn(), onConvert: vi.fn(), onReview: vi.fn(), onPreview: vi.fn(), onDownload: vi.fn(), onSend: vi.fn() });

it("compacta las acciones y conserva aceptar, revisión y nueva versión", async () => {
  const actions = callbacks();
  render(<QuotationRowActions {...actions} number="COT-01" status="negotiating" version={2} canWrite busy={false} />);
  const group = screen.getByRole("group", { name: "Acciones de COT-01" });
  expect(within(group).getAllByRole("button")).toHaveLength(3);
  fireEvent.click(screen.getByRole("button", { name: "Aceptar cotización" }));
  expect(actions.onAccept).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", { name: "Versiones y negociación" }));
  expect(actions.onReview).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", { name: "Más acciones" }));
  const menu = screen.getByRole("menu");
  expect(group.contains(menu)).toBe(false);
  fireEvent.click(within(menu).getByRole("menuitem", { name: "Nueva versión · v3" }));
  expect(actions.onVersion).toHaveBeenCalledOnce();
  expect(screen.queryByRole("menu")).toBeNull();
});

it("respeta lectura y operaciones ocupadas", () => {
  const actions = callbacks();
  const { rerender } = render(<QuotationRowActions {...actions} number="COT-02" status="accepted" version={1} canWrite={false} busy={false} />);
  expect(screen.queryByRole("button", { name: "Convertir a pedido" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Más acciones" }));
  expect(screen.queryByRole("menuitem", { name: "Enviar cotización" })).toBeNull();
  expect(screen.getByRole("menuitem", { name: "Descargar PDF" })).toBeTruthy();
  rerender(<QuotationRowActions {...actions} number="COT-02" status="accepted" version={1} canWrite busy />);
  fireEvent.click(screen.getByRole("button", { name: "Convertir a pedido" }));
  expect(actions.onConvert).not.toHaveBeenCalled();
});

it("navega con teclado y cierra con Escape o clic exterior", async () => {
  render(<QuotationRowActions {...callbacks()} number="COT-03" status="converted" version={1} canWrite busy={false} />);
  const trigger = screen.getByRole("button", { name: "Más acciones" });
  fireEvent.keyDown(trigger, { key: "ArrowDown" });
  const menu = screen.getByRole("menu");
  await waitFor(() => expect(document.activeElement).toBe(screen.getByRole("menuitem", { name: "Vista previa" })));
  fireEvent.keyDown(menu, { key: "ArrowDown" });
  expect(document.activeElement).toBe(screen.getByRole("menuitem", { name: "Descargar PDF" }));
  fireEvent.keyDown(menu, { key: "Escape" });
  expect(screen.queryByRole("menu")).toBeNull();
  expect(document.activeElement).toBe(trigger);
  fireEvent.click(trigger);
  fireEvent.pointerDown(document.body);
  expect(screen.queryByRole("menu")).toBeNull();
});

it("muestra ayudas del sistema con cursor y teclado sin el title nativo", () => {
  render(<QuotationRowActions {...callbacks()} number="COT-04" status="pending" version={1} canWrite busy={false} />);
  const review = screen.getByRole("button", { name: "Versiones y negociación" });
  expect(review.hasAttribute("title")).toBe(false);
  fireEvent.mouseEnter(review);
  const tip = screen.getByRole("tooltip");
  expect(tip.textContent).toBe("Versiones y negociación");
  expect(review.getAttribute("aria-describedby")).toBe(tip.id);
  expect(screen.getByRole("group", { name: "Acciones de COT-04" }).contains(tip)).toBe(false);
  fireEvent.mouseLeave(review);
  expect(screen.queryByRole("tooltip")).toBeNull();
  fireEvent.focus(review);
  expect(screen.getByRole("tooltip").textContent).toBe("Versiones y negociación");
  fireEvent.keyDown(review, { key: "Escape" });
  expect(screen.queryByRole("tooltip")).toBeNull();
});
