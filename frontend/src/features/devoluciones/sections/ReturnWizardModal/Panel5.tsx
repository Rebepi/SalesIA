import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";
import { Check, ShieldAlert } from "lucide-react";
import { EligibleLine } from "../../types/ReturnWizardModal";

export function Panel5({ selectedItems, creditAction, estimatedRefundTotal, currency }: { creditAction: ReturnType<typeof useReturnWizardModal>["creditAction"] } & { selectedItems: EligibleLine[]; estimatedRefundTotal: number; currency: string }) {
  return (<div className="space-y-6">
    <div className="grid grid-cols-2 gap-4">
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
        <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 uppercase tracking-wider">
          <Check className="h-4 w-4" />
          Partes listas para procesar
        </div>
        <ul className="mt-3 space-y-2 text-xs text-emerald-900">
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
            <span>{selectedItems.length} producto(s) clasificados</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
            <span>Destino físico validado para cada línea</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
            <span>Mecanismo comercial {creditAction} seleccionado</span>
          </li>
        </ul>
      </div>

      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
        <div className="flex items-center gap-2 text-xs font-bold text-amber-800 uppercase tracking-wider">
          <ShieldAlert className="h-4 w-4" />
          Partes pendientes posteriores
        </div>
        <ul className="mt-3 space-y-2 text-xs text-amber-900">
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
            <span>Ingreso efectivo a estantería de almacén</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
            <span>Conciliación contable en cierre diario</span>
          </li>
        </ul>
      </div>
    </div>

    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs">
      <div className="flex justify-between py-1">
        <span className="text-slate-600">Subtotal de devolución:</span>
        <span className="font-semibold text-slate-800">{currency} {estimatedRefundTotal.toFixed(2)}</span>
      </div>
      <div className="flex justify-between py-1 border-t border-slate-200 mt-2 pt-2 text-sm">
        <span className="font-bold text-slate-900">Total a liquidar:</span>
        <span className="font-bold text-teal-800">{currency} {estimatedRefundTotal.toFixed(2)}</span>
      </div>
    </div>
  </div>);
}
