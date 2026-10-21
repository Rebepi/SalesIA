import type { usePricingAndPromotionsTab } from "../../hooks/usePricingAndPromotionsTab";
import { Flame, X } from "lucide-react";

export function SeccionCrearCampanaDePromocion({ newPromoModalOpen, handleCreatePromotion, setNewPromoModalOpen, newPromoCode, setNewPromoCode, newPromoName, setNewPromoName, newPromoDiscount, setNewPromoDiscount, newPromoPriority, setNewPromoPriority, newPromoExclusive, setNewPromoExclusive, busy }: { newPromoModalOpen: ReturnType<typeof usePricingAndPromotionsTab>["newPromoModalOpen"]; handleCreatePromotion: ReturnType<typeof usePricingAndPromotionsTab>["handleCreatePromotion"]; setNewPromoModalOpen: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoModalOpen"]; newPromoCode: ReturnType<typeof usePricingAndPromotionsTab>["newPromoCode"]; setNewPromoCode: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoCode"]; newPromoName: ReturnType<typeof usePricingAndPromotionsTab>["newPromoName"]; setNewPromoName: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoName"]; newPromoDiscount: ReturnType<typeof usePricingAndPromotionsTab>["newPromoDiscount"]; setNewPromoDiscount: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoDiscount"]; newPromoPriority: ReturnType<typeof usePricingAndPromotionsTab>["newPromoPriority"]; setNewPromoPriority: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoPriority"]; newPromoExclusive: ReturnType<typeof usePricingAndPromotionsTab>["newPromoExclusive"]; setNewPromoExclusive: ReturnType<typeof usePricingAndPromotionsTab>["setNewPromoExclusive"]; busy: ReturnType<typeof usePricingAndPromotionsTab>["busy"] }) {
  return (<div
    className={newPromoModalOpen ? "fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs" : "hidden"}
    role="dialog"
    aria-modal="true"
    aria-labelledby="promo-modal-title"
  >
    <form
      onSubmit={async (e) => {
        await handleCreatePromotion(e);
        setNewPromoModalOpen(false);
      }}
      className="app-modal-panel w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-2xl space-y-4 text-xs text-slate-900 dark:text-slate-100"
    >
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <h3 id="promo-modal-title" className="text-sm font-bold text-slate-900 dark:text-white">
              Crear Campaña de Promoción
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Define un descuento porcentual y su prioridad de aplicación.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setNewPromoModalOpen(false)}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-200 transition"
          aria-label="Cerrar"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Código de Campaña
          </label>
          <input
            required
            placeholder="Ej. CYBER20"
            value={newPromoCode}
            onChange={e => setNewPromoCode(e.target.value)}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500 uppercase font-mono font-bold"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Nombre descriptivo
          </label>
          <input
            required
            placeholder="Ej. Promo Verano 2026"
            value={newPromoName}
            onChange={e => setNewPromoName(e.target.value)}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Descuento (%)
          </label>
          <input
            required
            type="number"
            min="0" max="100" step="0.01"
            value={newPromoDiscount}
            onChange={e => setNewPromoDiscount(e.target.value)}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500"
          />
        </div>
        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Prioridad de Aplicación
          </label>
          <input
            required
            type="number"
            value={newPromoPriority}
            onChange={e => setNewPromoPriority(e.target.value)}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500"
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-slate-600 dark:text-slate-300 text-xs py-1 cursor-pointer">
        <input
          type="checkbox"
          checked={newPromoExclusive}
          onChange={e => setNewPromoExclusive(e.target.checked)}
          className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
        />
        <span>Promoción exclusiva (rechaza otros descuentos simultáneos)</span>
      </label>

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
        <button
          type="button"
          onClick={() => setNewPromoModalOpen(false)}
          className="rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-2 font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-teal-600 hover:bg-teal-500 px-4 py-2 font-semibold text-white transition disabled:opacity-50"
        >
          {busy ? "Registrando…" : "Registrar Campaña"}
        </button>
      </div>
    </form>
  </div>);
}
