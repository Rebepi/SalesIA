import type { usePricingAndPromotionsTab } from "../../hooks/usePricingAndPromotionsTab";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Calculator, AlertCircle, ChevronUp } from "lucide-react";

export function SeccionSimuladorDeReglasYConflicto({ setShowSimulator, simProductId, setSimProductId, setSimResult, simProducts, simQuantity, setSimQuantity, simSelectedList, setSimSelectedList, simCustomers, simCouponCode, setSimCouponCode, runSimulation, simating, simResult }: { setShowSimulator: ReturnType<typeof usePricingAndPromotionsTab>["setShowSimulator"]; simProductId: ReturnType<typeof usePricingAndPromotionsTab>["simProductId"]; setSimProductId: ReturnType<typeof usePricingAndPromotionsTab>["setSimProductId"]; setSimResult: ReturnType<typeof usePricingAndPromotionsTab>["setSimResult"]; simProducts: ReturnType<typeof usePricingAndPromotionsTab>["simProducts"]; simQuantity: ReturnType<typeof usePricingAndPromotionsTab>["simQuantity"]; setSimQuantity: ReturnType<typeof usePricingAndPromotionsTab>["setSimQuantity"]; simSelectedList: ReturnType<typeof usePricingAndPromotionsTab>["simSelectedList"]; setSimSelectedList: ReturnType<typeof usePricingAndPromotionsTab>["setSimSelectedList"]; simCustomers: ReturnType<typeof usePricingAndPromotionsTab>["simCustomers"]; simCouponCode: ReturnType<typeof usePricingAndPromotionsTab>["simCouponCode"]; setSimCouponCode: ReturnType<typeof usePricingAndPromotionsTab>["setSimCouponCode"]; runSimulation: ReturnType<typeof usePricingAndPromotionsTab>["runSimulation"]; simating: ReturnType<typeof usePricingAndPromotionsTab>["simating"]; simResult: ReturnType<typeof usePricingAndPromotionsTab>["simResult"] }) {
  return (<section className="rounded-2xl border border-teal-500/30 bg-white dark:bg-slate-900/90 p-4 sm:p-5 shadow-lg shadow-black/10 dark:shadow-black/25 backdrop-blur-xs space-y-3.5 transition-all">
    <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2.5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20">
          <Calculator className="h-4 w-4" />
        </div>
        <h3 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white">
          Simulador de Reglas y Conflicto de Precios
        </h3>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden sm:inline-block text-[11px] text-slate-500 dark:text-slate-400">
          Cálculo en tiempo real
        </span>
        <button
          type="button"
          onClick={() => setShowSimulator(false)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-800/80 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
        >
          <ChevronUp className="h-3.5 w-3.5" />
          Ocultar simulador
        </button>
      </div>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
      <div>
        <label className="block font-semibold text-slate-600 dark:text-slate-300 mb-1" htmlFor="sim-product">
          Producto
        </label>
        <CustomSelect remote={{ resource: "products" }}
          searchable
          id="sim-product"
          value={simProductId}
          onChange={event => { setSimProductId(event.target.value); setSimResult(null); }}
          className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:border-teal-500"
        >
          <option value="">Selecciona un producto</option>
          {simProducts.map(product => (
            <option key={product.id} value={product.id}>
              {product.name} · {product.sku}
            </option>
          ))}
        </CustomSelect>
      </div>
      <div>
        <label className="block font-semibold text-slate-600 dark:text-slate-300 mb-1">
          Cantidad Estimada
        </label>
        <input
          type="number"
          min="1"
          value={simQuantity}
          onChange={e => { setSimQuantity(e.target.value); setSimResult(null); }}
          className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500"
        />
      </div>
      <div>
        <label className="block font-semibold text-slate-600 dark:text-slate-300 mb-1">
          Cliente / Lista asignada
        </label>
        <CustomSelect remote={{ resource: "customers" }}
          value={simSelectedList}
          onChange={e => { setSimSelectedList(e.target.value); setSimResult(null); }}
          className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:border-teal-500"
        >
          <option value="">Sin cliente (precio general)</option>
          {simCustomers.map(customer => (
            <option key={customer.id} value={customer.id}>
              {customer.legal_name}
            </option>
          ))}
        </CustomSelect>
      </div>
      <div>
        <label className="block font-semibold text-slate-600 dark:text-slate-300 mb-1">
          Código de Promoción / Cupón
        </label>
        <input
          placeholder="Ej. PROMO10"
          value={simCouponCode}
          onChange={e => { setSimCouponCode(e.target.value); setSimResult(null); }}
          className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-slate-900 dark:text-white outline-none focus:border-teal-500"
        />
      </div>
    </div>

    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
      <button
        type="button"
        onClick={runSimulation}
        disabled={simating || !simProductId || Number(simQuantity) <= 0}
        className="inline-flex items-center gap-1.5 rounded-xl bg-teal-600 hover:bg-teal-500 px-4 py-2 text-xs font-bold text-white shadow-sm transition disabled:opacity-50"
      >
        <Calculator className="h-3.5 w-3.5" />
        {simating ? "Calculando…" : "Calcular precio"}
      </button>
      {simResult && (
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-500 dark:text-slate-400">
            Descuento aplicado:{" "}
            <strong className="text-slate-800 dark:text-slate-200">${simResult.discount.toFixed(2)}</strong>
          </span>
          <span className="text-sm sm:text-base font-extrabold text-teal-600 dark:text-teal-400">
            Total Simulado: ${simResult.finalPrice.toFixed(2)}
          </span>
        </div>
      )}
    </div>

    {simResult?.conflict && (
      <div role="alert" className="flex items-center gap-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 p-3 text-xs text-amber-900 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
        <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
        <span>{simResult.conflict}</span>
      </div>
    )}
  </section>);
}
