import { describe, it, expect } from "vitest";
import { renderToString } from "react-dom/server";
import { ToastProvider } from "../toast/ToastContext";
import { ReturnWizardModal } from "../../features/devoluciones/components/ReturnWizardModal";

describe("RET-014: UI de Asistente de Devolucion y Experiencia Visual", () => {
  it("renders null modal body when modal is closed", () => {
    const html = renderToString(
      <ToastProvider>
        <ReturnWizardModal
          isOpen={false}
          onClose={() => {}}
          saleId="00000000-0000-0000-0000-000000000001"
          documentNumber="BV01-100200"
          customerName="Comercial Andina SAC"
        />
      </ToastProvider>
    );
    expect(html).not.toContain("Asistente de Devolución Comercial");
    expect(html).not.toContain("role=\"dialog\"");
  });

  it("renders wizard header, document number, customer, and step indicators when open", () => {
    const html = renderToString(
      <ToastProvider>
        <ReturnWizardModal
          isOpen={true}
          onClose={() => {}}
          saleId="00000000-0000-0000-0000-000000000001"
          documentNumber="BV01-100200"
          customerName="Comercial Andina SAC"
        />
      </ToastProvider>
    );
    expect(html).toContain("Asistente de Devolución Comercial");
    expect(html).toContain("BV01-100200");
    expect(html).toContain("Comercial Andina SAC");
    expect(html).toContain("1. Productos");
    expect(html).toContain("2. Destino físico");
    expect(html).toContain("3. Crédito y Dinero");
    expect(html).toContain("4. Resumen");
  });

  it("contains navigation elements and accessible dialog markup", () => {
    const html = renderToString(
      <ToastProvider>
        <ReturnWizardModal
          isOpen={true}
          onClose={() => {}}
          saleId="00000000-0000-0000-0000-000000000001"
          documentNumber="BV01-100200"
          customerName="Comercial Andina SAC"
        />
      </ToastProvider>
    );
    expect(html).toContain("role=\"dialog\"");
    expect(html).toContain("aria-labelledby=\"return-wizard-title\"");
    expect(html).toContain("aria-modal=\"true\"");
  });
});
