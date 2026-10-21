import { SeccionSimuladorDeReglasYConflicto } from "../sections/PricingAndPromotionsTab/SeccionSimuladorDeReglasYConflicto";
import { SeccionListasDePreciosYVigencias } from "../sections/PricingAndPromotionsTab/SeccionListasDePreciosYVigencias";
import { SeccionEliminar } from "../sections/PricingAndPromotionsTab/SeccionEliminar";
import { SeccionCrearCampanaDePromocion } from "../sections/PricingAndPromotionsTab/SeccionCrearCampanaDePromocion";
import { usePricingAndPromotionsTab } from "../hooks/usePricingAndPromotionsTab";
import { Calculator, AlertCircle, LoaderCircle, X, Trash2, Pencil } from "lucide-react";
import { RemoteEntitySelect } from "../../../ui/components/RemoteEntitySelect";
import { ProductChoice } from "../types/PricingAndPromotionsTab";
import { productPriceOption } from "../support/PricingAndPromotionsTab";

export function PricingAndPromotionsTab({ canWrite = true }: { canWrite?: boolean }) {
  const { PromptDialogNode, priceLists, promotions, loading, error, showSimulator, setShowSimulator, newPromoModalOpen, setNewPromoModalOpen, confirmDelete, setConfirmDelete, simProductId, setSimProductId, simProducts, simCustomers, simating, simQuantity, setSimQuantity, simSelectedList, setSimSelectedList, simCouponCode, setSimCouponCode, simResult, setSimResult, newPromoCode, setNewPromoCode, newPromoName, setNewPromoName, newPromoDiscount, setNewPromoDiscount, newPromoPriority, setNewPromoPriority, newPromoExclusive, setNewPromoExclusive, busy, managedList, setManagedList, priceItems, selectedProduct, setSelectedProduct, newFixedPrice, setNewFixedPrice, newDiscount, setNewDiscount, newListOpen, setNewListOpen, loadData, runSimulation, handleCreatePromotion, handleTogglePromotion, handleDeletePromotion, handleTogglePriceList, handleDeletePriceList, openPriceList, updateManagedList, addPriceItem, deletePriceItem, updatePriceItem, createPriceList } = usePricingAndPromotionsTab({ canWrite });
  return (
    <div id="scr-012-pricing-and-promotions" className="space-y-4 w-full max-w-full">
      <h1 className="sr-only">Precios y Promociones</h1>

      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 p-4 text-xs text-red-800 dark:text-red-200">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 shrink-0" />
          <div className="flex-1">
            <p className="font-semibold">{error}</p>
            <button type="button" onClick={loadData} className="mt-1 font-bold underline">Reintentar</button>
          </div>
        </div>
      )}

      {showSimulator ? (
        <SeccionSimuladorDeReglasYConflicto setShowSimulator={setShowSimulator} simProductId={simProductId} setSimProductId={setSimProductId} setSimResult={setSimResult} simProducts={simProducts} simQuantity={simQuantity} setSimQuantity={setSimQuantity} simSelectedList={simSelectedList} setSimSelectedList={setSimSelectedList} simCustomers={simCustomers} simCouponCode={simCouponCode} setSimCouponCode={setSimCouponCode} runSimulation={runSimulation} simating={simating} simResult={simResult} />
      ) : (
        <div className="flex items-center justify-between rounded-xl border border-teal-500/30 bg-white dark:bg-slate-900/80 px-4 py-2.5 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20">
              <Calculator className="h-4 w-4" />
            </div>
            <span className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white">
              Simulador de Reglas y Conflicto de Precios
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowSimulator(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-teal-500/30 bg-teal-50 dark:bg-teal-500/10 px-3 py-1.5 text-xs font-semibold text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-500/20 transition"
          >
            <Calculator className="h-3.5 w-3.5" />
            Mostrar simulador
          </button>
        </div>
      )}

      {loading ? (
        <div role="status" className="flex justify-center py-20 text-slate-400">
          <LoaderCircle className="h-8 w-8 motion-safe:animate-spin text-teal-600" />
        </div>
      ) : (
        <SeccionListasDePreciosYVigencias priceLists={priceLists} canWrite={canWrite} setNewListOpen={setNewListOpen} openPriceList={openPriceList} handleTogglePriceList={handleTogglePriceList} setConfirmDelete={setConfirmDelete} promotions={promotions} setNewPromoModalOpen={setNewPromoModalOpen} handleTogglePromotion={handleTogglePromotion} />
      )}

      {newListOpen && <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 p-4"><form onSubmit={createPriceList} className="app-modal-panel w-full max-w-2xl space-y-4 rounded-3xl bg-white p-6 shadow-2xl dark:bg-slate-900"><div className="flex justify-between"><div><h3 className="font-bold dark:text-white">Nueva lista de precios</h3><p className="text-xs text-slate-500">Define moneda, prioridad, vigencia y alcance.</p></div><button type="button" onClick={() => setNewListOpen(false)}><X className="h-5 w-5" /></button></div><div className="grid gap-3 sm:grid-cols-2"><label className="text-xs font-semibold dark:text-slate-300">Código<input name="code" required className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Nombre<input name="name" required className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Moneda<input name="currency" required defaultValue="USD" maxLength={3} className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Prioridad<input name="priority" type="number" min="1" defaultValue="10" className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Alcance<select name="target_type" className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950"><option value="all">General</option><option value="segment">Segmento</option><option value="branch">Sucursal</option><option value="customer">Cliente</option></select></label><label className="text-xs font-semibold dark:text-slate-300">Código del alcance<input name="target_id" placeholder="Opcional para lista general" className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Desde<input name="valid_from" type="date" className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="text-xs font-semibold dark:text-slate-300">Hasta<input name="valid_to" type="date" className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label></div><div className="flex justify-end"><button className="rounded-xl bg-teal-700 px-5 py-2 text-xs font-semibold text-white">Crear lista</button></div></form></div>}

      {managedList && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"><div className="app-modal-panel w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-slate-900"><header className="flex items-center justify-between border-b p-5 dark:border-slate-800"><div><h3 className="font-bold dark:text-white">Gestionar {managedList.name}</h3><p className="text-xs text-slate-500">Productos, precios, vigencia, prioridad, moneda y alcance.</p></div><button type="button" onClick={() => setManagedList(null)}><X className="h-5 w-5" /></button></header><div className="max-h-[78vh] space-y-5 overflow-y-auto p-5"><form onSubmit={updateManagedList} className="grid gap-3 rounded-2xl border p-4 text-xs dark:border-slate-700 sm:grid-cols-4"><label className="font-semibold dark:text-slate-300">Nombre<input name="name" required defaultValue={managedList.name} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><label className="font-semibold dark:text-slate-300">Moneda<input name="currency" defaultValue={managedList.currency} maxLength={3} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><label className="font-semibold dark:text-slate-300">Prioridad<input name="priority" type="number" min="1" defaultValue={managedList.priority} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><label className="font-semibold dark:text-slate-300">Alcance<select name="target_type" defaultValue={managedList.target_type || "all"} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950"><option value="all">General</option><option value="segment">Segmento</option><option value="branch">Sucursal</option><option value="customer">Cliente</option></select></label><label className="font-semibold dark:text-slate-300">Objetivo<input name="target_id" defaultValue={managedList.target_id || ""} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><label className="font-semibold dark:text-slate-300">Desde<input name="valid_from" type="date" defaultValue={managedList.valid_from?.substring(0, 10)} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><label className="font-semibold dark:text-slate-300">Hasta<input name="valid_to" type="date" defaultValue={managedList.valid_to?.substring(0, 10)} className="mt-1 w-full rounded-xl border p-2 dark:border-slate-700 dark:bg-slate-950" /></label><button type="submit" className="self-end rounded-xl bg-teal-700 px-4 py-2 font-semibold text-white">Guardar configuración</button></form><section className="rounded-2xl border p-4 dark:border-slate-700"><h4 className="mb-3 font-bold dark:text-white">Agregar producto</h4><div className="grid grid-cols-12 items-end gap-2 text-xs"><RemoteEntitySelect<ProductChoice> className="col-span-6" value={selectedProduct?.id || ""} onChange={(_, option) => setSelectedProduct(option?.data)} endpoint="/api/v1/products" entityType="product" mapOption={productPriceOption} initialOption={selectedProduct ? productPriceOption(selectedProduct) : undefined} label="Producto" placeholder="Buscar SKU o nombre" /><label className="col-span-2 font-semibold dark:text-slate-300">Precio fijo<input type="number" min="0" step="any" value={newFixedPrice} onChange={event => setNewFixedPrice(event.target.value)} className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><label className="col-span-2 font-semibold dark:text-slate-300">Descuento %<input type="number" min="0" max="100" step="any" value={newDiscount} onChange={event => setNewDiscount(event.target.value)} className="mt-1 w-full rounded-xl border p-2.5 dark:border-slate-700 dark:bg-slate-950" /></label><button type="button" onClick={addPriceItem} disabled={!selectedProduct || (!newFixedPrice && !newDiscount)} className="col-span-2 rounded-xl bg-teal-700 px-3 py-2.5 font-semibold text-white disabled:opacity-40">Agregar</button></div></section><div className="overflow-hidden rounded-2xl border dark:border-slate-700"><table className="w-full text-left text-xs"><thead className="bg-slate-50 text-slate-500 dark:bg-slate-800"><tr><th className="p-3">Producto</th><th className="p-3">Base</th><th className="p-3">Precio fijo</th><th className="p-3">Descuento</th><th className="p-3"></th></tr></thead><tbody className="divide-y dark:divide-slate-700">{priceItems.map(item => <tr key={item.id}><td className="p-3"><strong className="block dark:text-white">{item.product_name}</strong><span className="font-mono text-slate-500">{item.sku}</span></td><td className="p-3">{item.base_price}</td><td className="p-3">{item.fixed_price || "—"}</td><td className="p-3">{item.discount_percentage ? `${Number(item.discount_percentage) * 100}%` : "—"}</td><td className="p-3 text-right"><div className="inline-flex items-center gap-3"><button type="button" onClick={() => updatePriceItem(item)} className="text-teal-600" aria-label={`Editar precio de ${item.product_name}`}><Pencil className="h-4 w-4" /></button><button type="button" onClick={() => deletePriceItem(item.id)} className="text-rose-600" aria-label={`Quitar ${item.product_name} de la lista`}><Trash2 className="h-4 w-4" /></button></div></td></tr>)}</tbody></table>{!priceItems.length && <p className="p-8 text-center text-xs text-slate-500">Todavía no hay productos en esta lista.</p>}</div></div></div></div>}

      {confirmDelete && (
        <SeccionEliminar confirmDelete={confirmDelete} setConfirmDelete={setConfirmDelete} busy={busy} handleDeletePromotion={handleDeletePromotion} handleDeletePriceList={handleDeletePriceList} />
      )}

      {canWrite && (
        <SeccionCrearCampanaDePromocion newPromoModalOpen={newPromoModalOpen} handleCreatePromotion={handleCreatePromotion} setNewPromoModalOpen={setNewPromoModalOpen} newPromoCode={newPromoCode} setNewPromoCode={setNewPromoCode} newPromoName={newPromoName} setNewPromoName={setNewPromoName} newPromoDiscount={newPromoDiscount} setNewPromoDiscount={setNewPromoDiscount} newPromoPriority={newPromoPriority} setNewPromoPriority={setNewPromoPriority} newPromoExclusive={newPromoExclusive} setNewPromoExclusive={setNewPromoExclusive} busy={busy} />
      )}
      {PromptDialogNode}
    </div>
  );
}
