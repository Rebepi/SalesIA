import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";
import { CheckCircle2 } from "lucide-react";
import { ReturnWizardModalProps } from "../../types/ReturnWizardModal";

export function SeccionDevolucionConfirmadaConExito({ generatedReturnId, creditAction, onClose, currency, finalValuation, finalSettlement, hideClose = false }: { generatedReturnId: ReturnType<typeof useReturnWizardModal>["generatedReturnId"]; creditAction: ReturnType<typeof useReturnWizardModal>["creditAction"] } & { hideClose?: boolean; onClose: ReturnWizardModalProps["onClose"]; currency: string; finalValuation: { retained_total: string; refundable_total: string } | null; finalSettlement: { available_amount: string; movements: { kind: string; amount: string }[] } | null }) {
  return (<div data-testid="return-success-animated" className="flex flex-col items-center justify-center py-4 text-center">
    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shadow-inner">
      <CheckCircle2 className="h-7 w-7 motion-safe:animate-pulse" />
    </div>
    <h3 className="mt-4 text-xl font-bold text-slate-900">Devolución confirmada con éxito</h3>
    <p className="mt-2 text-sm text-slate-600">
      Identificador de devolución registrado:{" "}
      <span className="font-mono font-medium text-slate-900">{generatedReturnId}</span>
    </p>
    <div className="mt-6 w-full max-w-md rounded-xl border border-slate-200 bg-slate-50 p-4 text-left text-xs space-y-2">
      <div className="flex justify-between">
        <span className="text-slate-500">Efecto comercial:</span>
        <span className="font-semibold text-emerald-700">Completado y reflejado</span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-500">Mecanismo financiero:</span>
        <span className="font-semibold text-slate-800">
          {creditAction === "CREDIT_NOTE"
            ? "Nota de crédito generada"
            : creditAction === "STORE_CREDIT"
              ? (finalSettlement?.movements.some(item => item.kind === "store_credit") ? "Saldo a favor abonado a cuenta" : "Valor aplicado a la deuda de la venta")
              : "Pendiente de registrar el reembolso"}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-slate-500">Destino físico:</span>
        <span className="font-semibold text-slate-800">Aceptado según peritaje</span>
      </div>
    </div>
    {finalSettlement && <div className="mt-4 space-y-1 text-sm text-slate-700">{finalSettlement.movements.map((item, index) => <p key={index}>{item.kind === "debt_offset" ? "Aplicado a deuda original" : item.kind === "store_credit" ? "Otorgado como saldo a favor" : item.kind}: {currency} {item.amount}</p>)}<p>Disponible para otra liquidación: {currency} {finalSettlement.available_amount}</p></div>}
    {finalValuation && <p className="mt-4 text-sm text-slate-700">Retención aplicada: {currency} {finalValuation.retained_total} · Importe valorado: {currency} {finalValuation.refundable_total}</p>}
    {!hideClose && <div className="mt-8">
      <button
        type="button"
        onClick={onClose}
        className="rounded-xl bg-teal-700 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 focus:outline-none focus:ring-4 focus:ring-teal-100"
      >
        Cerrar asistente
      </button>
    </div>}
  </div>);
}
