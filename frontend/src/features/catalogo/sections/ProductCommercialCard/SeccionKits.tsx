import type { useProductCommercialCard } from "../../hooks/useProductCommercialCard";
import { CustomSelect } from "../../../../ui/components/CustomSelect";
import { Plus } from "lucide-react";
import { Props } from "../../types/ProductCommercialCard";
import { inputStyle } from "../../support/ProductCommercialCard";
import { btnPrimary } from "../../support/ProductCommercialCard";

export function SeccionKits({ canWrite, handleAddKitItem, allProducts, productId, productData }: { handleAddKitItem: ReturnType<typeof useProductCommercialCard>["handleAddKitItem"]; productData: NonNullable<ReturnType<typeof useProductCommercialCard>["productData"]> } & { canWrite: Props["canWrite"]; allProducts: Props["allProducts"]; productId: Props["productId"] }) {
  return (<div className="space-y-6">
    {canWrite && (
      <form onSubmit={handleAddKitItem} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Agregar componente a este combo o kit</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <CustomSelect remote={{ resource: "products", exclude_id: productId }} name="component_product_id" required className={inputStyle}>
            <option value="">Selecciona componente...</option>
            {allProducts.filter(p => p.id !== productId).map(p => (
              <option key={String(p.id)} value={String(p.id)}>{String(p.name)} ({String(p.sku)})</option>
            ))}
          </CustomSelect>
          <input name="quantity" type="number" step="any" placeholder="Cantidad consumida por kit" required className={inputStyle} />
        </div>
        <div className="mt-3 flex justify-end">
          <button type="submit" className={btnPrimary}>
            <Plus className="h-4 w-4" /> Agregar componente
          </button>
        </div>
      </form>
    )}

    <div className="overflow-hidden rounded-xl border border-slate-200">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-100 uppercase text-slate-500">
          <tr>
            <th className="p-3">ID Componente</th>
            <th className="p-3">Cantidad consumida</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {productData.kit_items.length === 0 ? (
            <tr>
              <td colSpan={2} className="p-6 text-center text-slate-400">Este producto no está configurado como kit o combo</td>
            </tr>
          ) : (
            productData.kit_items.map((item, i) => (
              <tr key={String(item.id || i)}>
                <td className="p-3 font-mono">{String(item.component_product_id)}</td>
                <td className="p-3 font-semibold">{String(item.quantity)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>);
}
