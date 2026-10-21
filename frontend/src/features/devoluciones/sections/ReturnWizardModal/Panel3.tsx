import type { useReturnWizardModal } from "../../hooks/useReturnWizardModal";
import { Package } from "lucide-react";
import { EligibleLine } from "../../types/ReturnWizardModal";

export function Panel3({ selectedItems, quantities, dispositions, handleDispositionChange }: { quantities: ReturnType<typeof useReturnWizardModal>["quantities"]; dispositions: ReturnType<typeof useReturnWizardModal>["dispositions"] } & { selectedItems: EligibleLine[]; handleDispositionChange: (productId: string, disp: "RESTOCK" | "QUARANTINE" | "DISPOSE") => void }) {
  return (<div className="space-y-5">
    <div className="rounded-xl border border-amber-100 bg-amber-50/60 p-4 text-xs text-amber-900">
      Define la inspección física y el destino de cada producto devuelto. Solo la mercancía clasificada
      como vendible (RESTOCK) volverá al inventario disponible.
    </div>

    <div className="space-y-3">
      {selectedItems.map((line) => (
        <div key={line.sale_line_id || line.product_id} className="rounded-xl border border-slate-200 p-4 bg-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold text-sm text-slate-900">{line.product_name}</div>
              <div className="text-xs text-slate-500">
                Cantidad a recibir: {quantities[line.sale_line_id || line.product_id]} unidades
              </div>
            </div>
            <Package className="h-5 w-5 text-slate-400" />
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {[
              { id: "RESTOCK", label: "Restock Vendible", color: "border-emerald-300 text-emerald-800" },
              { id: "QUARANTINE", label: "Cuarentena / Daño", color: "border-amber-300 text-amber-800" },
              { id: "DISPOSE", label: "Baja / Merma", color: "border-red-300 text-red-800" }
            ].map((disp) => {
              const isSelected = (dispositions[line.sale_line_id || line.product_id] || "RESTOCK") === disp.id;
              return (
                <button
                  type="button"
                  key={disp.id}
                  aria-pressed={isSelected}
                  onClick={() =>
                    handleDispositionChange(
                      line.sale_line_id || line.product_id,
                      disp.id as "RESTOCK" | "QUARANTINE" | "DISPOSE"
                    )
                  }
                  className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${isSelected
                    ? `bg-teal-50 border-teal-600 text-teal-900 ring-2 ring-teal-200`
                    : "border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100"
                    }`}
                >
                  {disp.label}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  </div>);
}
