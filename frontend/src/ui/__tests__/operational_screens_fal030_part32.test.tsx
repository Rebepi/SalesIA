import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastProvider } from "../toast/ToastContext";
import { PaymentConfirmationModal } from "../../features/ventas/components/PaymentConfirmationModal";
import { AccountsReceivableTab } from "../../features/cuentas_cobrar/components/AccountsReceivableTab";
import { CashRegisterWorkspaceTab } from "../../features/caja/components/CashRegisterWorkspaceTab";
import { InventoryWorkspaceTab, TransferItem, CountItem } from "../../features/inventario/components/InventoryWorkspaceTab";
import { PurchasesWorkspaceTab, PurchaseOrder } from "../../features/compras/components/PurchasesWorkspaceTab";
import { DeliveriesWorkspaceTab } from "../../features/logistica/components/DeliveriesWorkspaceTab";
import { ReturnWizardModal } from "../../features/devoluciones/components/ReturnWizardModal";
import { RefundsWorkspaceTab } from "../../features/devoluciones/components/RefundsWorkspaceTab";

const mockTransferItem1: TransferItem = {
  id: "trf-1",
  document_number: "TRF-001",
  source_warehouse_id: "wh-1",
  destination_warehouse_id: "wh-2",
  status: "in_transit",
  lines: [
    {
      product_id: "p1",
      product_name: "Prod 1",
      quantity: "10",
      processed_quantity: "0",
      damaged_quantity: "0",
      unit_cost: "5"
    }
  ],
  created_at: "2026-10-10T10:00:00Z"
};

const mockTransferItem2: TransferItem = {
  id: "trf-2",
  document_number: "TRF-002",
  source_warehouse_id: "wh-1",
  destination_warehouse_id: "wh-2",
  status: "partially_received",
  lines: [
    {
      product_id: "p1",
      product_name: "Prod 1",
      quantity: "10",
      processed_quantity: "5",
      damaged_quantity: "1",
      unit_cost: "5"
    }
  ],
  created_at: "2026-10-10T10:00:00Z"
};

const mockCount1: CountItem = {
  id: "cnt-1",
  warehouse_id: "wh-1",
  status: "APPROVED",
  notes: null,
  cutoff_at: "2026-10-10T10:00:00Z",
  created_at: "2026-10-10T10:00:00Z",
  lines: []
};

const mockCount2: CountItem = {
  id: "cnt-2",
  warehouse_id: "wh-1",
  status: "IN_PROGRESS",
  notes: null,
  cutoff_at: "2026-10-10T10:00:00Z",
  created_at: "2026-10-10T10:00:00Z",
  lines: []
};

const mockPurchaseOrder: PurchaseOrder = {
  id: "po-1",
  document_number: "OC-2026-0001",
  supplier_id: "sup-1",
  warehouse_id: "wh-1",
  status: "approved",
  version: 1,
  lines: [
    {
      product_id: "p1",
      product_name: "Prod 1",
      quantity: "10",
      processed_quantity: "0",
      damaged_quantity: "0",
      unit_cost: "20"
    }
  ],
  created_at: "2026-10-10T10:00:00Z"
};

const testQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
});

function wrap(ui: React.ReactElement): string {
  return renderToString(
    <QueryClientProvider client={testQueryClient}>
      <ToastProvider>
        {ui}
      </ToastProvider>
    </QueryClientProvider>
  );
}

describe("SCR-018: Cobro — diálogo con saldo, método, referencia y estados", () => {
  it("renders dialog with id scr-018-payment-dialog when open", () => {
    const html = wrap(
      <PaymentConfirmationModal
        isOpen={true}
        amount={250.00}
        currency="USD"
        customerName="Distribuidora Morales SAC"
        documentNumber="F001-000123"
        paymentMethod="TRANSFER"
        balance={500.00}
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("scr-018-payment-dialog");
  });

  it("shows balance field when balance prop is provided", () => {
    const html = wrap(
      <PaymentConfirmationModal
        isOpen={true}
        amount={100.00}
        currency="PEN"
        customerName="Cliente ABC"
        documentNumber="B001-000010"
        paymentMethod="CASH"
        balance={100.00}
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("confirm-balance");
    expect(html).toContain("100.00");
  });

  it("shows reference code input field with prefilled value", () => {
    const html = wrap(
      <PaymentConfirmationModal
        isOpen={true}
        amount={300.00}
        currency="USD"
        customerName="Empresa XYZ"
        documentNumber="F002-000050"
        paymentMethod="CARD"
        referenceCode="TXN-998877"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("confirm-reference-input");
    expect(html).toContain("TXN-998877");
  });

  it("displays pending status badge by default", () => {
    const html = wrap(
      <PaymentConfirmationModal
        isOpen={true}
        amount={75.50}
        currency="USD"
        customerName="Test Client"
        documentNumber="F001-000001"
        paymentMethod="CASH"
        initialStatus="pending"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("payment-status-badge");
    expect(html).toContain("Pendiente");
  });

  it("does not render when isOpen is false", () => {
    const html = wrap(
      <PaymentConfirmationModal
        isOpen={false}
        amount={100.00}
        currency="USD"
        customerName="Test"
        documentNumber="F001-000001"
        paymentMethod="CASH"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).not.toContain("scr-018-payment-dialog");
  });
});

describe("SCR-019: Cuentas por cobrar — tabla de antigüedad con buckets y reconciliación", () => {
  it("renders container with id scr-019-receivables-tab", () => {
    const html = wrap(<AccountsReceivableTab canWrite={true} />);
    expect(html).toContain("scr-019-receivables-tab");
  });

  it("shows aging bucket summary panel headers for all 4 buckets", () => {
    const html = wrap(<AccountsReceivableTab />);
    expect(html).toContain("0 a 30 días");
    expect(html).toContain("31 a 60 días");
    expect(html).toContain("61 a 90 días");
    expect(html).toContain("Más de 90 días");
  });

  it("has filter buttons for each aging bucket", () => {
    const html = wrap(<AccountsReceivableTab />);
    expect(html).toContain("0-30 días");
    expect(html).toContain("31-60 días");
    expect(html).toContain("61-90 días");
    expect(html).toContain("90+ días");
  });

  it("renders the total cartera exigible and en disputa summary", () => {
    const html = wrap(<AccountsReceivableTab />);
    expect(html).toContain("Total Cartera Exigible");
    expect(html).toContain("En Disputa");
  });

  it("shows receivables table with invoice, date, balance columns", () => {
    const html = wrap(<AccountsReceivableTab />);
    expect(html).toContain("Comprobante");
    expect(html).toContain("Saldo Pendiente");
    expect(html).toContain("Antigüedad");
  });

  it("has reconcile actions column header in table", () => {
    const html = wrap(<AccountsReceivableTab />);
    expect(html).toContain("Acciones");
  });
});

describe("SCR-020: Caja — apertura, movimientos, arqueo ciego, diferencia, cierre", () => {
  it("renders container with id scr-020-cash-register-tab", () => {
    const html = wrap(<CashRegisterWorkspaceTab canWrite={true} />);
    expect(html).toContain("scr-020-cash-register-tab");
  });

  it("shows open session button when no active session and canWrite is true", () => {
    const html = wrap(<CashRegisterWorkspaceTab canWrite={true} />);
    expect(html).toContain("open-session-btn");
    expect(html).toContain("Abrir Turno");
  });

  it("shows title about caja and arqueo ciego workflow", () => {
    const html = wrap(<CashRegisterWorkspaceTab />);
    expect(html).toContain("Caja y Arqueo Ciego");
    expect(html).toContain("arqueo de valores");
  });

  it("shows no sessions placeholder when list is empty", () => {
    const html = wrap(<CashRegisterWorkspaceTab canWrite={false} />);
    expect(html).toContain("No hay turnos de caja");
  });

  it("shows opening form fields when modal open button is in document", () => {
    const html = wrap(<CashRegisterWorkspaceTab canWrite={true} />);
    expect(html).toContain("Abrir Turno de Caja");
  });
});

describe("SCR-021: Existencias — tabla producto/almacén con físico, reservado, disponible, cuarentena", () => {
  it("renders stock section with id scr-021-inventory-stock when default submodule is stock", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} />);
    expect(html).toContain("scr-021-inventory-stock");
  });

  it("shows stock table column headers for all quantity types", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} />);
    expect(html).toContain("Físico");
    expect(html).toContain("Reservado");
    expect(html).toContain("Disponible");
    expect(html).toContain("Cuarentena");
  });

  it("shows KPI summary cards with stock type labels", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} />);
    expect(html).toContain("Vendible Disponible");
    expect(html).toContain("Reservado por Ventas");
    expect(html).toContain("En Tránsito Transferencias");
    expect(html).toContain("Retenido en Cuarentena");
  });
});

describe("SCR-022: Kardex — movimientos con saldo progresivo y apertura de documento origen", () => {
  it("renders kardex section with id scr-022-kardex-tab in the page", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} initialSubmodule="kardex" />);
    expect(html).toContain("scr-022-kardex-tab");
  });

  it("shows kardex table columns for movement and balance tracking", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} initialSubmodule="kardex" />);
    expect(html).toContain("Variación");
    expect(html).toContain("Saldo Físico");
    expect(html).toContain("Costo Promedio");
  });
});

describe("SCR-023: Transferencias — editor origen/destino con tránsito, recepción parcial, daño", () => {
  it("renders transfers section with id scr-023-transfers-tab", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} initialSubmodule="transfers" />);
    expect(html).toContain("scr-023-transfers-tab");
  });

  it("shows transfer status values in_transit and partially_received in the page", () => {
    const html = wrap(
      <InventoryWorkspaceTab
        canWrite={false}
        initialSubmodule="transfers"
        initialTransfers={[mockTransferItem1, mockTransferItem2]}
      />
    );
    expect(html).toContain("in_transit");
    expect(html).toContain("partially_received");
  });
});

describe("SCR-024: Conteos — sesión de captura con segregación ingreso físico / aprobación ajuste", () => {
  it("renders counts section with id scr-024-counts-tab", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} initialSubmodule="counts" />);
    expect(html).toContain("scr-024-counts-tab");
  });

  it("shows count status labels APPROVED and IN_PROGRESS", () => {
    const html = wrap(
      <InventoryWorkspaceTab
        canWrite={false}
        initialSubmodule="counts"
        initialCounts={[mockCount1, mockCount2]}
      />
    );
    expect(html).toContain("APPROVED");
    expect(html).toContain("IN_PROGRESS");
  });

  it("shows blind count session description text", () => {
    const html = wrap(<InventoryWorkspaceTab canWrite={false} initialSubmodule="counts" />);
    expect(html).toContain("Sesiones de conteo ciego");
  });
});

describe("SCR-025: Proveedores — listado con ficha, condiciones, validación de duplicados", () => {
  it("renders suppliers section with id scr-025-suppliers-tab", () => {
    const html = wrap(<PurchasesWorkspaceTab canWrite={false} initialSubtab="suppliers" />);
    expect(html).toContain("scr-025-suppliers-tab");
  });

  it("shows supplier table headers including RUC and Banco fields", () => {
    const html = wrap(<PurchasesWorkspaceTab canWrite={false} initialSubtab="suppliers" />);
    expect(html).toContain("RUC");
    expect(html).toContain("Banco");
  });
});

describe("SCR-026: Compras — orden con líneas, aprobaciones, recepciones vinculadas", () => {
  it("renders purchase orders section with id scr-026-purchases-tab", () => {
    const html = wrap(<PurchasesWorkspaceTab canWrite={false} />);
    expect(html).toContain("scr-026-purchases-tab");
  });

  it("shows order table columns Estado and Versión for approval tracking", () => {
    const html = wrap(<PurchasesWorkspaceTab canWrite={false} />);
    expect(html).toContain("Estado");
    expect(html).toContain("Versión");
  });
});

describe("SCR-027: Recepciones — cantidades, lotes/series, errores por línea, rechazo sobrerecepciones", () => {
  it("renders reception modal with id scr-027-receptions-modal", () => {
    const html = wrap(
      <PurchasesWorkspaceTab
        canWrite={false}
        initialModalType="receive_goods"
        initialActiveOrder={mockPurchaseOrder}
      />
    );
    expect(html).toContain("scr-027-receptions-modal");
  });

  it("loads inspection options from the order before showing quantities", () => {
    const html = wrap(
      <PurchasesWorkspaceTab
        canWrite={false}
        initialModalType="receive_goods"
        initialActiveOrder={mockPurchaseOrder}
      />
    );
    expect(html).toContain("Cargando saldos y recepciones anteriores");
    expect(html).not.toContain("Confirmar Recepción");
  });

  it("offers a balance refresh when receiving data has not loaded", () => {
    const html = wrap(
      <PurchasesWorkspaceTab
        canWrite={false}
        initialModalType="receive_goods"
        initialActiveOrder={mockPurchaseOrder}
      />
    );
    expect(html).toContain("Actualizar saldos");
  });
});

describe("SCR-028: Entregas — lista por estado con evidencia POD y transportista", () => {
  it("renders deliveries tab with id scr-028-deliveries-tab", () => {
    const html = wrap(<DeliveriesWorkspaceTab canWrite={false} />);
    expect(html).toContain("scr-028-deliveries-tab");
  });

  it("shows delivery status filter options", () => {
    const html = wrap(<DeliveriesWorkspaceTab canWrite={false} />);
    expect(html).toContain("Despachado");
    expect(html).toContain("En Tránsito");
    expect(html).toContain("Entregado");
  });

  it("shows carrier filter options for transportista selection", () => {
    const html = wrap(<DeliveriesWorkspaceTab canWrite={false} />);
    expect(html).toContain("DHL Express");
    expect(html).toContain("FedEx");
  });

  it("shows filter button for delayed deliveries only", () => {
    const html = wrap(<DeliveriesWorkspaceTab canWrite={false} />);
    expect(html).toContain("Solo Atrasadas");
  });
});

describe("SCR-029: Devoluciones — selección de venta con máx devolvible, motivo, destino físico", () => {
  it("renders return wizard with id scr-029-return-wizard when isOpen is true", () => {
    const html = wrap(
      <ReturnWizardModal
        isOpen={true}
        onClose={() => {}}
        saleId="test-sale-id-001"
        documentNumber="F001-000999"
        customerName="Cliente Devolución SA"
      />
    );
    expect(html).toContain("scr-029-return-wizard");
  });

  it("shows return wizard title about Devolución Comercial", () => {
    const html = wrap(
      <ReturnWizardModal
        isOpen={true}
        onClose={() => {}}
        saleId="test-sale-id-002"
        documentNumber="F001-001000"
        customerName="Cliente"
      />
    );
    expect(html).toContain("Devolución Comercial");
  });

  it("returns empty content when isOpen is false", () => {
    const html = wrap(
      <ReturnWizardModal
        isOpen={false}
        onClose={() => {}}
        saleId="test-sale-id-003"
        documentNumber="F001-000001"
        customerName="Cliente"
      />
    );
    expect(html).not.toContain("scr-029-return-wizard");
  });

  it("shows document number and customer name in wizard header at step 1", () => {
    const html = wrap(
      <ReturnWizardModal
        isOpen={true}
        onClose={() => {}}
        saleId="test-sale-id-004"
        documentNumber="F001-000001"
        customerName="Test"
      />
    );
    expect(html).toContain("F001-000001");
    expect(html).toContain("Test");
  });
});

describe("SCR-030: Reembolsos — cola por estado con incertidumbre de proveedor y anti-duplicados", () => {
  it("renders refunds tab with id scr-030-refunds-tab", () => {
    const html = wrap(<RefundsWorkspaceTab canWrite={true} />);
    expect(html).toContain("scr-030-refunds-tab");
  });

  it("shows status filter buttons for all refund lifecycle states", () => {
    const html = wrap(<RefundsWorkspaceTab />);
    expect(html).toContain("Solicitados");
    expect(html).toContain("Aprobados");
    expect(html).toContain("Enviados a pasarela");
    expect(html).toContain("Pendientes");
    expect(html).toContain("Confirmados");
    expect(html).toContain("Incertidumbre");
    expect(html).toContain("Fallidos");
  });

  it("shows request refund button with proper test id", () => {
    const html = wrap(<RefundsWorkspaceTab canWrite={true} />);
    expect(html).toContain("request-refund-btn");
    expect(html).toContain("Solicitar Reembolso");
  });

  it("shows refund table with all required column headers", () => {
    const html = wrap(<RefundsWorkspaceTab />);
    expect(html).toContain("ID Reembolso");
    expect(html).toContain("Pago Origen");
    expect(html).toContain("Estado");
    expect(html).toContain("Referencia Proveedor");
  });

  it("shows main tab description mentioning prevention of duplicates", () => {
    const html = wrap(<RefundsWorkspaceTab canWrite={true} />);
    expect(html).toContain("prevención de duplicados");
  });
});
