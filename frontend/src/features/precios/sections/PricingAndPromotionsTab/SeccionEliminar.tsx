import type { usePricingAndPromotionsTab } from "../../hooks/usePricingAndPromotionsTab";
import { Trash2 } from "lucide-react";

export function SeccionEliminar({ confirmDelete, setConfirmDelete, busy, handleDeletePromotion, handleDeletePriceList }: { confirmDelete: NonNullable<ReturnType<typeof usePricingAndPromotionsTab>["confirmDelete"]>; setConfirmDelete: ReturnType<typeof usePricingAndPromotionsTab>["setConfirmDelete"]; busy: ReturnType<typeof usePricingAndPromotionsTab>["busy"]; handleDeletePromotion: ReturnType<typeof usePricingAndPromotionsTab>["handleDeletePromotion"]; handleDeletePriceList: ReturnType<typeof usePricingAndPromotionsTab>["handleDeletePriceList"] }) {
  return (<div
    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs"
    role="dialog"
    aria-modal="true"
  >
    <div className="app-modal-panel w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-2xl space-y-4 text-xs text-slate-900 dark:text-slate-100">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 shrink-0">
          <Trash2 className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            ¿Eliminar {confirmDelete.type === "promo" ? "campaña" : "lista de precios"}?
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {confirmDelete.code} · {confirmDelete.name}
          </p>
        </div>
      </div>

      <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
        {confirmDelete.type === "promo"
          ? "Esta promoción no registra transacciones aplicadas, por lo que es seguro eliminarla de forma definitiva."
          : "Esta lista de precios será eliminada junto con sus reglas configuradas."}
      </p>

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
        <button
          type="button"
          onClick={() => setConfirmDelete(null)}
          className="rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-2 font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
        >
          Cancelar
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            if (confirmDelete.type === "promo") {
              handleDeletePromotion(confirmDelete.id, confirmDelete.code);
            } else {
              handleDeletePriceList(confirmDelete.id, confirmDelete.code);
            }
          }}
          className="rounded-xl bg-rose-600 hover:bg-rose-500 px-4 py-2 font-semibold text-white transition disabled:opacity-50"
        >
          {busy ? "Eliminando…" : "Eliminar definitivamente"}
        </button>
      </div>
    </div>
  </div>);
}
