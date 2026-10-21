import { ReturnHelp } from "../../components/ReturnHelp";
import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";
import { DollarSign, Receipt, RotateCcw } from "lucide-react";

export function Panel4({ estimatedRefundTotal, creditAction, setCreditAction, currency, canGrantStoreCredit }: { creditAction: ReturnType<typeof useReturnWizardModal>["creditAction"]; setCreditAction: ReturnType<typeof useReturnWizardModal>["setCreditAction"]; estimatedRefundTotal: number; currency: string; canGrantStoreCredit: boolean }) {
  return <div className="space-y-5">
    <div className="sales-return-mechanism rounded-xl border p-4 text-sm">Importe estimado después de retenciones e impuestos: <strong>{currency} {estimatedRefundTotal.toFixed(2)}</strong>. El servidor calcula el importe definitivo al aceptar.</div>
    <p className="text-sm text-slate-500">Se compensa primero la deuda de la venta original. Elige cómo usar el valor restante. Se generará una nota de crédito comercial interna; este proceso no confirma una emisión electrónica ante SUNAT.</p>
    <fieldset className="space-y-3"><legend className="mb-2 text-sm font-semibold">Destino del valor de la devolución <ReturnHelp title="Destino del valor de la devolución" description="Primero se compensa la deuda de la venta. El resto puede conservarse para un cambio o reembolso, u otorgarse como saldo a favor. El dinero no se desembolsa al seleccionar una opción; se registra después de aceptar la devolución." /></legend>
      {[
        { id: "CREDIT_NOTE" as const, title: "Ajustar deuda y conservar valor para un cambio", desc: "Conserva el excedente en la liquidación. Después podrás elegir productos de reemplazo, reembolsar o conceder saldo a favor.", icon: Receipt },
        { id: "STORE_CREDIT" as const, title: "Saldo a favor del cliente", desc: "Otorga el excedente como crédito del cliente en esta moneda para sus próximas compras.", icon: DollarSign },
        { id: "REFUND" as const, title: "Reembolso de dinero", desc: "Después de aceptar, elige el pago original y registra el desembolso. En efectivo se exige una caja abierta autorizada.", icon: RotateCcw }
      ].map(option => <label key={option.id} className="return-financial-choice"><option.icon className="mt-1 h-5 w-5 shrink-0 text-teal-600" /><span className="flex-1"><strong>{option.title}</strong><span className="mt-1 block text-xs text-slate-500">{option.desc}</span></span><input type="radio" name="creditAction" value={option.id} checked={creditAction === option.id} disabled={option.id === "STORE_CREDIT" && !canGrantStoreCredit} onChange={() => setCreditAction(option.id)} /></label>)}
    </fieldset>
  </div>;
}
