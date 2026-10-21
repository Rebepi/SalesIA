import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import type { ComponentProps } from "react";
import { Panel2 } from "../src/features/pedidos/sections/OrdersWorkspaceTab/Panel2";

afterEach(cleanup);

function setup(status: string, canWrite = true, busy = false) {
  const order = { order_id: "o1", order_number: "PED-1", customer_id: "c1", customer_name: "Cliente", total_amount: "100", currency: "PEN", status, stock_reserved: status === "confirmed" };
  const props = { orders: [order], canWrite, busy, handleConfirmAndReserve: vi.fn(), orderAction: vi.fn(), openFulfillModal: vi.fn(), openShortages: vi.fn(), setSelectedOrder: vi.fn() } as unknown as ComponentProps<typeof Panel2>;
  render(<Panel2 {...props} />);
  return { props, order };
}

it("reserva y abre el detalle con iconos y ayuda del sistema", () => {
  const { props, order } = setup("draft");
  const reserve = screen.getByRole("button", { name: "Reservar stock" });
  expect(reserve.textContent).toBe("");
  expect(reserve.hasAttribute("title")).toBe(false);
  fireEvent.mouseEnter(reserve);
  expect(screen.getByRole("tooltip").textContent).toBe("Reservar stock");
  fireEvent.click(reserve);
  expect(props.handleConfirmAndReserve).toHaveBeenCalledWith(order);
  fireEvent.click(screen.getByRole("button", { name: "Ver detalle del pedido" }));
  expect(props.setSelectedOrder).toHaveBeenCalledWith(order);
});

it("conserva aprobación, despacho y restricciones por estado", () => {
  let result = setup("pending_approval");
  fireEvent.click(screen.getByRole("button", { name: "Aprobar pedido" }));
  expect(result.props.orderAction).toHaveBeenCalledWith(result.order, "approve");
  expect(screen.queryByRole("button", { name: "Reservar stock" })).toBeNull();
  cleanup();
  result = setup("confirmed");
  fireEvent.click(screen.getByRole("button", { name: "Despachar pedido" }));
  expect(result.props.openFulfillModal).toHaveBeenCalledWith(result.order);
  fireEvent.focus(screen.getByRole("button", { name: "Más opciones" }));
  expect(screen.getByRole("tooltip").textContent).toBe("Más opciones");
  fireEvent.click(screen.getByRole("button", { name: "Más opciones" }));
  fireEvent.click(screen.getByRole("button", { name: "Repetir pedido" }));
  expect(result.props.orderAction).toHaveBeenCalledWith(result.order, "clone");
});

it("respeta permisos y estado ocupado sin modificar controles de paginación", () => {
  setup("draft", false);
  expect(screen.queryByRole("button", { name: "Reservar stock" })).toBeNull();
  const row = screen.getByText("PED-1").closest("tr")!;
  expect(within(row).getAllByRole("button")).toHaveLength(2);
  cleanup();
  const { props } = setup("draft", true, true);
  const button = screen.getByRole("button", { name: "Reservar stock" }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  fireEvent.click(button);
  expect(props.handleConfirmAndReserve).not.toHaveBeenCalled();
});
