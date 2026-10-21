import type { usePurchasesWorkspaceTab } from "../../hooks/usePurchasesWorkspaceTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { X } from "lucide-react";
import { ModalSurface } from "../../../../ui/components/ModalSurface";

export function SeccionLanded_cost({ receiptActionBusy, setModalType, handleLandedCost, receiptSelector, activeOrder, selectedReceipt }: { receiptActionBusy: ReturnType<typeof usePurchasesWorkspaceTab>["receiptActionBusy"]; setModalType: ReturnType<typeof usePurchasesWorkspaceTab>["setModalType"]; handleLandedCost: ReturnType<typeof usePurchasesWorkspaceTab>["handleLandedCost"]; receiptSelector: ReturnType<typeof usePurchasesWorkspaceTab>["receiptSelector"]; activeOrder: ReturnType<typeof usePurchasesWorkspaceTab>["activeOrder"]; selectedReceipt: ReturnType<typeof usePurchasesWorkspaceTab>["selectedReceipt"] }) {
  return (<ModalSurface labelledBy="landed-cost-title" blocked={receiptActionBusy} onClose={() => setModalType(null)}>
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 id="landed-cost-title" className="font-bold text-slate-900">Costos de Adquisición / Prorrateo</h3>
        <button disabled={receiptActionBusy} onClick={() => setModalType(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100"><X className="h-4 w-4" /></button>
      </div>
      <form onSubmit={handleLandedCost} className="mt-4 space-y-3">
        {receiptSelector()}
        <label className="block text-xs font-semibold text-slate-700">
          Tipo de Cargo Adicional
          <CustomSelect name="charge_type" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
            <option value="FREIGHT">Flete / Transporte Internacional</option>
            <option value="CUSTOMS">Aranceles e Impuestos Aduaneros</option>
            <option value="INSURANCE">Seguro de Carga</option>
            <option value="HANDLING">Manipuleo y Almacenaje</option>
          </CustomSelect>
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Monto del cargo ({activeOrder?.details?.currency || "moneda de compra"})
          <input name="amount" type="number" step="0.01" min="0.01" required placeholder="150.00" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Método de Prorrateo
          <CustomSelect name="allocation_method" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs">
            <option value="VALUE">Por Valor de las Líneas</option>
            <option value="QUANTITY">Por Cantidad de Unidades</option>
          </CustomSelect>
        </label>
        <label className="block text-xs font-semibold text-slate-700">
          Observaciones / Referencia
          <input name="notes" placeholder="Factura de flete marítimo" className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs" />
        </label>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" disabled={receiptActionBusy} onClick={() => setModalType(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700">Cancelar</button>
          <button type="submit" disabled={!selectedReceipt || receiptActionBusy} className="rounded-xl bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:opacity-50">Aplicar Costos</button>
        </div>
      </form>
    </div>
  </ModalSurface>);
}
