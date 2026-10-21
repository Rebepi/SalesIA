import { PackageCheck, Wallet, ClipboardCheck } from "lucide-react";
import type { EligibleLine } from "../../types/ReturnWizardModal";
import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";

export function Panel5({ selectedItems, creditAction, estimatedRefundTotal, currency, quantities, dispositions }: { creditAction: ReturnType<typeof useReturnWizardModal>["creditAction"]; selectedItems: EligibleLine[]; estimatedRefundTotal: number; currency: string; quantities: Record<string, number>; dispositions: Record<string, string> }) {
  const actionNames = { CREDIT_NOTE: "Ajustar deuda y conservar valor", STORE_CREDIT: "Saldo a favor del cliente", REFUND: "Reembolso de dinero" };
  const destinations: Record<string, string> = { RESTOCK: "Inventario vendible", QUARANTINE: "Cuarentena", DISPOSE: "Baja / merma" };
  return <section className="return-review space-y-5">
    <div className="return-section-heading"><span className="return-wizard-symbol"><ClipboardCheck size={20} /></span><div><h3>Revisa la devolución</h3><p>Comprueba los artículos y el destino del valor antes de continuar.</p></div></div>
    <div className="return-review-grid">
      <div className="return-review-card"><h4><PackageCheck size={17} /> Artículos a recibir <span>{selectedItems.length}</span></h4><div className="divide-y divide-slate-100">{selectedItems.map(line => {
        const key = line.sale_line_id || line.product_id;
        return <div key={key} className="return-review-line"><div><strong>{line.product_name}</strong><p>{line.sku} · {destinations[dispositions[key] || "RESTOCK"]}</p></div><span>{quantities[key]} un.</span></div>;
      })}</div></div>
      <div className="return-review-card"><h4><Wallet size={17} /> Liquidación</h4><strong className="return-review-destination">{actionNames[creditAction]}</strong><p className="return-review-copy">Primero se compensa la deuda de la venta. El excedente se aplica según la opción seleccionada.</p><div className="return-review-amount"><span>Importe estimado</span><strong>{currency} {estimatedRefundTotal.toLocaleString("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong><small>Incluye impuestos y retenciones aplicables.</small></div></div>
    </div>
  </section>;
}
