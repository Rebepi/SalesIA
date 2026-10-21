import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { PaymentConfirmationModal } from "../../features/ventas/components/PaymentConfirmationModal";

describe("PAY-020: UI de confirmacion de cobro irreversible", () => {
  it("renders null when modal is closed", () => {
    const html = renderToString(
      <PaymentConfirmationModal
        isOpen={false}
        amount="150.00"
        currency="USD"
        customerName="Corporacion Global SAC"
        documentNumber="F001-000045"
        paymentMethod="CASH"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toBe("");
  });

  it("presents amount, currency, customer, document, and method before action", () => {
    const html = renderToString(
      <PaymentConfirmationModal
        isOpen={true}
        amount="150.00"
        currency="USD"
        customerName="Corporacion Global SAC"
        documentNumber="F001-000045"
        paymentMethod="CASH"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("150.00");
    expect(html).toContain("USD");
    expect(html).toContain("Corporacion Global SAC");
    expect(html).toContain("F001-000045");
    expect(html).toContain("CASH");
    expect(html).toContain("Confirmar cobro");
    expect(html).not.toContain("data-testid=\"payment-success-animated\"");
  });

  it("formats numeric amounts properly in the dialog", () => {
    const html = renderToString(
      <PaymentConfirmationModal
        isOpen={true}
        amount={249.9}
        currency="PEN"
        customerName="Cliente Prueba"
        documentNumber="B001-000100"
        paymentMethod="TRANSFER"
        onConfirm={async () => {}}
        onClose={() => {}}
      />
    );
    expect(html).toContain("249.90");
    expect(html).toContain("PEN");
    expect(html).toContain("Cliente Prueba");
    expect(html).toContain("B001-000100");
    expect(html).toContain("TRANSFER");
  });
});
