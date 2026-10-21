import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";
import { Pencil } from "lucide-react";
import { IconAction } from "../src/ui/components/primitives/IconAction";
import { SeccionMembers } from "../src/features/seguridad/sections/UsersAndRolesWorkspaceTab/SeccionMembers";
import { Panel2 } from "../src/features/cuentas_cobrar/sections/AccountsReceivableTab/Panel2";
import { VentasBulkActionBar } from "../src/features/ventas/components/VentasBulkActionBar";

afterEach(cleanup);

it("ofrece ayuda fuera del contenedor, con cursor, foco y Escape", () => {
  const action = vi.fn();
  const { container } = render(<div style={{ overflow: "hidden" }}><IconAction label="Editar producto" onClick={action}><Pencil /></IconAction></div>);
  const button = screen.getByRole("button", { name: "Editar producto" });
  expect(button.textContent).toBe("");
  expect(button.hasAttribute("title")).toBe(false);
  fireEvent.mouseEnter(button);
  const tooltip = screen.getByRole("tooltip");
  expect(tooltip.textContent).toBe("Editar producto");
  expect(container.contains(tooltip)).toBe(false);
  expect(button.getAttribute("aria-describedby")).toBe(tooltip.id);
  fireEvent.mouseLeave(button);
  expect(screen.queryByRole("tooltip")).toBeNull();
  fireEvent.focus(button);
  expect(screen.getByRole("tooltip")).toBeTruthy();
  fireEvent.keyDown(button, { key: "Escape" });
  expect(screen.queryByRole("tooltip")).toBeNull();
  fireEvent.click(button);
  expect(action).toHaveBeenCalledOnce();
});

it("conserva las acciones de miembros y bloquea cambios sin permiso", () => {
  const member = { id: "m1", name: "Ana", email: "ana@example.test", status: "active", role_name: "Ventas", is_active: true };
  const props = { members: [member], canWrite: true, saving: false, handleResendInvitation: vi.fn(), setCancellingInvitation: vi.fn(), handleOpenEditor: vi.fn(), handleToggleActive: vi.fn() } as unknown as ComponentProps<typeof SeccionMembers>;
  const { rerender } = render(<SeccionMembers {...props} />);
  fireEvent.click(screen.getByRole("button", { name: "Editar Permisos" }));
  expect(props.handleOpenEditor).toHaveBeenCalledWith(member);
  fireEvent.click(screen.getByRole("button", { name: "Revisar baja" }));
  expect(props.handleToggleActive).toHaveBeenCalledWith(member);
  rerender(<SeccionMembers {...props} canWrite={false} />);
  fireEvent.click(screen.getByRole("button", { name: "Editar Permisos" }));
  expect(props.handleOpenEditor).toHaveBeenCalledTimes(1);
  expect((screen.getByRole("button", { name: "Revisar baja" }) as HTMLButtonElement).disabled).toBe(true);
});

it("distingue reenviar de cancelar invitación y respeta el estado ocupado", () => {
  const member = { id: "m2", name: "Luis", status: "invited", role_name: "Ventas" };
  const props = { members: [member], canWrite: true, saving: false, handleResendInvitation: vi.fn(), setCancellingInvitation: vi.fn(), handleOpenEditor: vi.fn(), handleToggleActive: vi.fn() } as unknown as ComponentProps<typeof SeccionMembers>;
  const { rerender } = render(<SeccionMembers {...props} />);
  fireEvent.click(screen.getByRole("button", { name: "Reenviar invitación" }));
  fireEvent.click(screen.getByRole("button", { name: "Cancelar invitación" }));
  expect(props.handleResendInvitation).toHaveBeenCalledWith(member);
  expect(props.setCancellingInvitation).toHaveBeenCalledWith(member);
  rerender(<SeccionMembers {...props} saving />);
  fireEvent.click(screen.getByRole("button", { name: "Cancelar invitación" }));
  expect(props.setCancellingInvitation).toHaveBeenCalledTimes(1);
});

it("mantiene cobro y conciliación del documento seleccionado", () => {
  const item = { sale_id: "s1", series_number: "F001-1", created_at: "2026-10-01", due_date: "2026-10-10", total_amount: "100", paid_amount: "20", balance_due: "80", currency: "PEN", aging_bucket: "0-30", selected_bucket_balance: null };
  const props = { filteredItems: [item], setAction: vi.fn(), canWrite: true, openReconciliation: vi.fn(), loading: false } as unknown as ComponentProps<typeof Panel2>;
  const { rerender } = render(<Panel2 {...props} />);
  const payment = screen.getByRole("button", { name: "Cobrar" });
  expect(payment.textContent).toBe("");
  fireEvent.click(payment);
  expect(props.setAction).toHaveBeenCalledWith({ saleId: "s1", mode: "payment" });
  fireEvent.click(screen.getByRole("button", { name: "Más opciones" }));
  fireEvent.click(screen.getByRole("button", { name: "Reconciliar" }));
  expect(props.openReconciliation).toHaveBeenCalledWith(item);
  rerender(<Panel2 {...props} canWrite={false} />);
  expect(screen.queryByRole("button", { name: "Cobrar" })).toBeNull();
});

it("conserva las seis operaciones de la barra masiva como iconos", () => {
  const props = { selectedCount: 3, onClearSelection: vi.fn(), onBatchPrint: vi.fn(), onBatchResend: vi.fn(), onExportSelected: vi.fn(), onAssignSeller: vi.fn(), onRetrySunat: vi.fn() };
  render(<VentasBulkActionBar {...props} />);
  const labels = ["Imprimir lote", "Reenviar", "Exportar", "Asignar vendedor", "Reintentar SUNAT", "Deseleccionar todos"];
  const callbacks = [props.onBatchPrint, props.onBatchResend, props.onExportSelected, props.onAssignSeller, props.onRetrySunat, props.onClearSelection];
  labels.forEach((label, index) => {
    const button = screen.getByRole("button", { name: label });
    expect(button.textContent).toBe("");
    expect(button.hasAttribute("title")).toBe(false);
    fireEvent.click(button);
    expect(callbacks[index]).toHaveBeenCalledOnce();
  });
});
